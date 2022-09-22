# -*- coding: utf-8 -*-
# Copyright 2021 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from bs4 import BeautifulSoup
from datetime import datetime

import graphene
from graphene.types import generic
from graphql import GraphQLError

from odoo import _
from odoo.http import request
from odoo.osv import expression
from odoo.addons.payment_vsf import utils as payment_utils
from odoo.addons.payment_vsf_adyen_direct.const import CURRENCY_DECIMALS
from odoo.addons.graphql_vuestorefront.schemas.objects import PaymentAcquirer, PaymentTransaction
from odoo.addons.graphql_vuestorefront.schemas.shop import Cart, CartData
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment_vsf_adyen_direct.controllers.main import AdyenDirectController


class PaymentAcquirerFilterInput(graphene.InputObjectType):
    order_id = graphene.Int()
    access_token = graphene.String()


class PaymentQuery(graphene.ObjectType):
    payment_acquirer = graphene.Field(
        PaymentAcquirer,
        required=True,
        id=graphene.Int(),
    )
    payment_acquirers = graphene.List(
        graphene.NonNull(PaymentAcquirer),
        filter=graphene.Argument(PaymentAcquirerFilterInput, default_value={}),
    )
    payment_confirmation = graphene.Field(
        Cart,
    )

    def resolve_payment_acquirer(self, info, id):
        domain = [
            ('id', '=', id),
            ('state', 'in', ['enabled', 'test']),
        ]
        payment_acquirer = info.context["env"]['payment.acquirer'].sudo().search(domain, limit=1)
        if not payment_acquirer:
            raise GraphQLError(_('Payment acquirer does not exist.'))
        return payment_acquirer

    def resolve_payment_acquirers(self, info, filter):
        env = info.context["env"]
        SaleOrder = env['sale.order'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        if filter.get('order_id', False):
            order = SaleOrder.search([('id', '=', filter['order_id'])], limit=1)

            if not order:
                raise GraphQLError(_('Order does not exist.'))

            if (not filter.get('access_token')) or \
                    (filter.get('access_token', False) and filter['access_token'] != order.sudo().access_token):
                raise GraphQLError(_("Sorry! You cannot access this Order."))

        if not order:
            raise GraphQLError(_('Order does not exist.'))

        domain = expression.AND([
            ['&', ('vsf_active', '=', True), ('state', 'in', ['enabled', 'test'])],
            ['|', ('company_id', '=', False), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', website.id)],
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [order.partner_id.country_id.id])]
        ])
        return env['payment.acquirer'].sudo().search(domain)

    def resolve_payment_confirmation(self, info):
        env = info.context["env"]

        PaymentTransaction = env['payment.transaction']
        Order = env['sale.order']

        # Pass in the session the sale_order created in vsf
        payment_transaction_id = request.session.get('__payment_tx_ids__')[0]

        if payment_transaction_id:
            payment_transaction = PaymentTransaction.sudo().search([('id', '=', payment_transaction_id)], limit=1)
            sale_order_id = payment_transaction.sale_order_ids.ids[0]

            if sale_order_id:
                order = Order.sudo().search([('id', '=', sale_order_id)], limit=1)

                if order.exists():
                    return CartData(order=order)

        raise GraphQLError(_('Cart does not exist'))


# --------------------------------------- #
#           Adyen Direct Payment          #
# --------------------------------------- #

class AdyenAcquirerInfoResult(graphene.ObjectType):
    adyen_acquirer_info = generic.GenericScalar()


class AdyenPaymentMethodsResult(graphene.ObjectType):
    adyen_payment_methods = generic.GenericScalar()


class AdyenTransactionResult(graphene.ObjectType):
    transaction = generic.GenericScalar()


class AdyenPaymentsResult(graphene.ObjectType):
    adyen_payments = generic.GenericScalar()


class AdyenPaymentDetailsResult(graphene.ObjectType):
    adyen_payment_details = generic.GenericScalar()


class AdyenAcquirerInfo(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)

    Output = AdyenAcquirerInfoResult

    @staticmethod
    def mutate(self, info, acquirer_id):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen_direct':
            raise GraphQLError(_('Payment acquirer with "adyen_direct" Provider does not exist.'))

        adyen_acquirer_info = AdyenDirectController().adyen_acquirer_info(
            acquirer_id=payment_acquirer_id.id
        )

        return AdyenAcquirerInfoResult(adyen_acquirer_info=adyen_acquirer_info)


class AdyenPaymentMethods(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)
        order_id = graphene.Int()

    Output = AdyenPaymentMethodsResult

    @staticmethod
    def mutate(self, info, acquirer_id, order_id):
        env = info.context["env"]
        SaleOrder = env['sale.order'].sudo()
        PaymentAcquirer = env['payment.acquirer'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        if order_id:
            order = SaleOrder.search([('id', '=', order_id)], limit=1)

        if not order:
            raise GraphQLError(_('Order does not exist.'))

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen_direct':
            raise GraphQLError(_('Payment acquirer with "adyen_direct" Provider does not exist.'))

        adyen_payment_methods = AdyenDirectController().adyen_payment_methods(
            acquirer_id=payment_acquirer_id.id,
            amount=order.amount_total,
            currency_id=order.currency_id.id,
            partner_id=order.partner_id.id
        )

        return AdyenPaymentMethodsResult(adyen_payment_methods=adyen_payment_methods)


class AdyenTransaction(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)
        order_id = graphene.Int()

    Output = AdyenTransactionResult

    @staticmethod
    def mutate(self, info, acquirer_id, order_id):
        env = info.context["env"]
        SaleOrder = env['sale.order'].sudo()
        PaymentAcquirer = env['payment.acquirer'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        if order_id:
            order = SaleOrder.search([('id', '=', order_id)], limit=1)

        if not order:
            raise GraphQLError(_('Order does not exist.'))

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen_direct':
            raise GraphQLError(_('Payment acquirer with "adyen_direct" Provider does not exist.'))

        transaction_form = WebsiteSale().payment_transaction(
            acquirer_id=acquirer_id,
            so_id=order.id,
            access_token=order.access_token
        ).decode('utf-8')

        # Get the Transaction Reference Value
        soup = BeautifulSoup(transaction_form, "lxml")
        transaction_reference = soup.find('input', {'name': 'reference'}).get('value')

        transaction_id = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)

        # Condition to Control the redirects
        if order_id:
            transaction_id.vsf_pay_by_link = True

        converted_amount = payment_utils.to_minor_currency_units(
            transaction_id.amount,
            transaction_id.currency_id,
            arbitrary_decimal_number=CURRENCY_DECIMALS.get(transaction_id.currency_id.name, 2)
        )

        access_token = payment_utils.generate_access_token(
            transaction_id.reference,
            converted_amount,
            transaction_id.partner_id.id
        )

        transaction = {
            'acquirer_id': transaction_id.acquirer_id.id,
            'provider': transaction_id.provider,
            'reference': transaction_id.reference,
            'amount': transaction_id.amount,
            'currency_id': transaction_id.currency_id.id,
            'partner_id': transaction_id.partner_id.id,
            'converted_amount': converted_amount,
            'access_token': access_token
        }

        return AdyenTransactionResult(transaction=transaction)


class AdyenPayments(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        access_token = graphene.String(required=True)
        payment_method = generic.GenericScalar(required=True, description='Return state.data.paymentMethod')
        browser_info = generic.GenericScalar(required=True, description='Return state.data.browserInfo')

    Output = AdyenPaymentsResult

    @staticmethod
    def mutate(self, info, acquirer_id, transaction_reference, access_token, payment_method, browser_info):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen_direct':
            raise GraphQLError(_('Payment acquirer with "adyen_direct" Provider does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        converted_amount = payment_utils.to_minor_currency_units(
            transaction.amount,
            transaction.currency_id,
            arbitrary_decimal_number=CURRENCY_DECIMALS.get(transaction.currency_id.name, 2)
        )

        # Create Payment
        adyen_payment = AdyenDirectController().adyen_payments(
            acquirer_id=payment_acquirer_id.id,
            reference=transaction.reference,
            converted_amount=converted_amount,
            currency_id=transaction.currency_id.id,
            partner_id=transaction.partner_id.id,
            payment_method=payment_method,
            access_token=access_token,
            browser_info=browser_info
        )

        return AdyenPaymentsResult(adyen_payments=adyen_payment)


class AdyenPaymentDetails(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        payment_details = generic.GenericScalar(required=True, description='Return state.data')

    Output = AdyenPaymentDetailsResult

    @staticmethod
    def mutate(self, info, acquirer_id, transaction_reference, payment_details):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen_direct':
            raise GraphQLError(_('Payment acquirer with "adyen_direct" Provider does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        # Submit the details
        adyen_payment_details = AdyenDirectController().adyen_payment_details(
            acquirer_id=payment_acquirer_id.id,
            reference=transaction.reference,
            payment_details=payment_details
        )

        return AdyenPaymentsResult(adyen_payment_details=adyen_payment_details)


class PaymentMutation(graphene.ObjectType):
    adyen_acquirer_info = AdyenAcquirerInfo.Field(description='Get Adyen Acquirer Info.')
    adyen_payment_methods = AdyenPaymentMethods.Field(description='Get Adyen Payment Methods.')
    adyen_transaction = AdyenTransaction.Field(description='Create Adyen Transaction')
    adyen_payments = AdyenPayments.Field(description='Make Adyen Payment request.')
    adyen_payment_details = AdyenPaymentDetails.Field(description='Submit the Adyen Payment Details.')
