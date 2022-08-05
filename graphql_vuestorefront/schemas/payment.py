# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _
from odoo.http import request
from odoo.osv import expression

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_adyen_og.const import SUPPORTED_CURRENCIES
from odoo.addons.graphql_vuestorefront.schemas.objects import PaymentAcquirer, PaymentTransaction
from odoo.addons.graphql_vuestorefront.schemas.shop import Cart, CartData
from odoo.addons.website_sale.controllers.main import PaymentPortal
from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.addons.payment_adyen_og.controllers.main import AdyenControllerInherit


class PaymentQuery(graphene.ObjectType):
    payment_acquirer = graphene.Field(
        PaymentAcquirer,
        required=True,
        id=graphene.Int(),
    )
    payment_acquirers = graphene.List(
        graphene.NonNull(PaymentAcquirer),
    )
    payment_confirmation = graphene.Field(
        Cart,
    )

    @staticmethod
    def resolve_payment_acquirer(self, info, id):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer:
            raise GraphQLError(_('Payment acquirer does not exist.'))
        return payment_acquirer

    @staticmethod
    def resolve_payment_acquirers(self, info):
        env = info.context["env"]

        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        domain = expression.AND([
            ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', website.id)],
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [order.partner_id.country_id.id])]
        ])
        return env['payment.acquirer'].sudo().search(domain)

    @staticmethod
    def resolve_payment_confirmation(self, info):
        env = info.context["env"]

        PaymentTransaction = env['payment.transaction']
        Order = env['sale.order']

        # Pass in the session the sale_order created in vsf
        payment_transaction_id = request.session.get('__payment_monitored_tx_ids__')

        if payment_transaction_id and payment_transaction_id[0]:
            payment_transaction = PaymentTransaction.sudo().search([('id', '=', payment_transaction_id[0])], limit=1)
            sale_order_id = payment_transaction.sale_order_ids.ids[0]

            if sale_order_id:
                order = Order.sudo().search([('id', '=', sale_order_id)], limit=1)

                if order.exists():
                    return CartData(order=order)

        raise GraphQLError(_('Cart does not exist'))


class MakePaymentResult(graphene.ObjectType):
    form = generic.GenericScalar()


class MakePayment(graphene.Mutation):
    class Arguments:
        payment_acquire_id = graphene.Int(required=True)

    Output = MakePaymentResult

    @staticmethod
    def mutate(self, info, payment_acquire_id):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        return MakePaymentResult(
            form=PaymentPortal().shop_payment_transaction(
                order_id=order.id,
                access_token=order.access_token,
                payment_option_id=payment_acquire_id,
                amount=order.amount_total,
                currency_id=order.currency_id.id,
                partner_id=order.partner_id.id,
                flow='redirect',
                tokenization_requested=False,
                landing_route='/shop/payment/validate'
            ).get('redirect_form_html')
        )


class MakeGiftCardPayment(graphene.Mutation):
    done = graphene.Boolean()

    @staticmethod
    def mutate(self, info):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        tx = order.get_portal_last_transaction()

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return MakeGiftCardPayment(done=True)

        return MakeGiftCardPayment(done=False)


class PaymentMutation(graphene.ObjectType):
    make_payment = MakePayment.Field(description='Creates a new payment request.')
    make_gift_card_payment = MakeGiftCardPayment.Field(description='Pay the order only with gift card.')


# -------------------------------- #
#           Adyen Payment          #
# -------------------------------- #

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

        if not payment_acquirer_id.provider == 'adyen':
            raise GraphQLError(_('Payment acquirer with "adyen" Provider does not exist.'))

        adyen_acquirer_info = AdyenController().adyen_acquirer_info(
            acquirer_id=payment_acquirer_id.id
        )

        return AdyenAcquirerInfoResult(adyen_acquirer_info=adyen_acquirer_info)


class AdyenPaymentMethods(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)

    Output = AdyenPaymentMethodsResult

    @staticmethod
    def mutate(self, info, acquirer_id):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen':
            raise GraphQLError(_('Payment acquirer with "adyen" Provider does not exist.'))

        adyen_payment_methods = AdyenController().adyen_payment_methods(
            acquirer_id=payment_acquirer_id.id,
            amount=order.amount_total,
            currency_id=order.currency_id.id,
            partner_id=order.partner_id.id
        )

        return AdyenPaymentMethodsResult(adyen_payment_methods=adyen_payment_methods)


class AdyenTransaction(graphene.Mutation):
    class Arguments:
        acquirer_id = graphene.Int(required=True)

    Output = AdyenTransactionResult

    @staticmethod
    def mutate(self, info, acquirer_id):
        env = info.context["env"]
        PaymentAcquirer = env['payment.acquirer'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', acquirer_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_acquirer_id = PaymentAcquirer.search(domain, limit=1)
        if not payment_acquirer_id:
            raise GraphQLError(_('Payment acquirer does not exist.'))

        if not payment_acquirer_id.provider == 'adyen':
            raise GraphQLError(_('Payment acquirer with "adyen" Provider does not exist.'))

        transaction = PaymentPortal().shop_payment_transaction(
            order_id=order.id,
            access_token=order.access_token,
            payment_option_id=acquirer_id,
            amount=order.amount_total,
            currency_id=order.currency_id.id,
            partner_id=order.partner_id.id,
            flow='direct',
            tokenization_requested=False,
            landing_route='/shop/payment/validate'
        )

        transaction_id = PaymentTransaction.search([('reference', '=', transaction['reference'])], limit=1)

        # Update the field created_on_vsf
        transaction_id.created_on_vsf = True

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

        if not payment_acquirer_id.provider == 'adyen':
            raise GraphQLError(_('Payment acquirer with "adyen" Provider does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        converted_amount = payment_utils.to_minor_currency_units(
            transaction.amount,
            transaction.currency_id,
            arbitrary_decimal_number=SUPPORTED_CURRENCIES.get(transaction.currency_id.name, 2)
        )

        # Create Payment
        adyen_payment = AdyenControllerInherit().adyen_payments(
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

        if not payment_acquirer_id.provider == 'adyen':
            raise GraphQLError(_('Payment acquirer with "adyen" Provider does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        # Submit the details
        adyen_payment_details = AdyenController().adyen_payment_details(
            acquirer_id=payment_acquirer_id.id,
            reference=transaction.reference,
            payment_details=payment_details
        )

        return AdyenPaymentsResult(adyen_payment_details=adyen_payment_details)


class AdyenPaymentMutation(graphene.ObjectType):
    adyen_acquirer_info = AdyenAcquirerInfo.Field(description='Get Adyen Acquirer Info.')
    adyen_payment_methods = AdyenPaymentMethods.Field(description='Get Adyen Payment Methods.')
    adyen_transaction = AdyenTransaction.Field(description='Create Adyen Transaction')
    adyen_payments = AdyenPayments.Field(description='Make Adyen Payment request.')
    adyen_payment_details = AdyenPaymentDetails.Field(description='Submit the Adyen Payment Details.')
