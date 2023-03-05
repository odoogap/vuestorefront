# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _
from odoo.http import request
from odoo.osv import expression

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_adyen_vsf.const import CURRENCY_DECIMALS
from odoo.addons.graphql_vuestorefront.schemas.objects import PaymentProvider, PaymentTransaction
from odoo.addons.graphql_vuestorefront.schemas.shop import Cart, CartData
from odoo.addons.website_sale.controllers.main import PaymentPortal
from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.addons.payment_adyen_vsf.controllers.main import AdyenControllerInherit


class PaymentQuery(graphene.ObjectType):
    payment_provider = graphene.Field(
        PaymentProvider,
        required=True,
        id=graphene.Int(),
    )
    payment_providers = graphene.List(
        graphene.NonNull(PaymentProvider),
    )
    payment_transaction = graphene.Field(
        PaymentTransaction,
        required=True,
        id=graphene.Int(default_value=None),
        reference=graphene.String(default_value=None)
    )
    payment_confirmation = graphene.Field(
        Cart,
    )

    @staticmethod
    def resolve_payment_provider(self, info, id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider = PaymentProvider.search(domain, limit=1)
        if not payment_provider:
            raise GraphQLError(_('Payment provider does not exist.'))
        return payment_provider

    @staticmethod
    def resolve_payment_providers(self, info):
        env = info.context["env"]

        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        domain = expression.AND([
            ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', website.id)],
            ['|', ('available_country_ids', '=', False), ('available_country_ids', 'in', [order.partner_id.country_id.id])]
        ])
        return env['payment.provider'].sudo().search(domain)

    @staticmethod
    def resolve_payment_transaction(self, info, id, reference):
        env = info.context["env"]
        PaymentTransaction = env['payment.transaction']

        if id:
            payment_transaction = PaymentTransaction.sudo().search([('id', '=', id)], limit=1)
        elif reference:
            payment_transaction = PaymentTransaction.sudo().search([('reference', '=', reference)], limit=1)
        else:
            payment_transaction = None

        if not payment_transaction:
            raise GraphQLError(_('Payment Transaction does not exist.'))
        return payment_transaction

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
    make_gift_card_payment = MakeGiftCardPayment.Field(description='Pay the order only with gift card.')


# -------------------------------- #
#           Adyen Payment          #
# -------------------------------- #

class AdyenProviderInfoResult(graphene.ObjectType):
    adyen_provider_info = generic.GenericScalar()


class AdyenPaymentMethodsResult(graphene.ObjectType):
    adyen_payment_methods = generic.GenericScalar()


class AdyenTransactionResult(graphene.ObjectType):
    transaction = generic.GenericScalar()


class AdyenPaymentsResult(graphene.ObjectType):
    adyen_payments = generic.GenericScalar()


class AdyenPaymentDetailsResult(graphene.ObjectType):
    adyen_payment_details = generic.GenericScalar()


class AdyenProviderInfo(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = AdyenProviderInfoResult

    @staticmethod
    def mutate(self, info, provider_id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'adyen':
            raise GraphQLError(_('Payment Provider "Adyen" does not exist.'))

        adyen_provider_info = AdyenController().adyen_provider_info(
            provider_id=payment_provider_id.id
        )

        return AdyenProviderInfoResult(adyen_provider_info=adyen_provider_info)


class AdyenPaymentMethods(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = AdyenPaymentMethodsResult

    @staticmethod
    def mutate(self, info, provider_id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'adyen':
            raise GraphQLError(_('Payment Provider "Adyen" does not exist.'))

        adyen_payment_methods = AdyenController().adyen_payment_methods(
            provider_id=payment_provider_id.id,
            amount=order.amount_total,
            currency_id=order.currency_id.id,
            partner_id=order.partner_id.id
        )

        return AdyenPaymentMethodsResult(adyen_payment_methods=adyen_payment_methods)


class AdyenTransaction(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = AdyenTransactionResult

    @staticmethod
    def mutate(self, info, provider_id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'adyen':
            raise GraphQLError(_('Payment Provider "Adyen" does not exist.'))

        transaction = PaymentPortal().shop_payment_transaction(
            order_id=order.id,
            access_token=order.access_token,
            payment_option_id=provider_id,
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
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        access_token = graphene.String(required=True)
        payment_method = generic.GenericScalar(required=True, description='Return state.data.paymentMethod')
        browser_info = generic.GenericScalar(required=True, description='Return state.data.browserInfo')

    Output = AdyenPaymentsResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference, access_token, payment_method, browser_info):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'adyen':
            raise GraphQLError(_('Payment Provider "Adyen" does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        converted_amount = payment_utils.to_minor_currency_units(
            transaction.amount,
            transaction.currency_id,
            arbitrary_decimal_number=CURRENCY_DECIMALS.get(transaction.currency_id.name, 2)
        )

        # Create Payment
        adyen_payment = AdyenControllerInherit().adyen_payments(
            provider_id=payment_provider_id.id,
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
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        payment_details = generic.GenericScalar(required=True, description='Return state.data')

    Output = AdyenPaymentDetailsResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference, payment_details):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        request.website = website
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'adyen':
            raise GraphQLError(_('Payment Provider "Adyen" does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        # Submit the details
        adyen_payment_details = AdyenController().adyen_payment_details(
            provider_id=payment_provider_id.id,
            reference=transaction.reference,
            payment_details=payment_details
        )

        return AdyenPaymentDetailsResult(adyen_payment_details=adyen_payment_details)


class AdyenPaymentMutation(graphene.ObjectType):
    adyen_provider_info = AdyenProviderInfo.Field(description='Get Adyen Provider Info.')
    adyen_payment_methods = AdyenPaymentMethods.Field(description='Get Adyen Payment Methods.')
    adyen_transaction = AdyenTransaction.Field(description='Create Adyen Transaction')
    adyen_payments = AdyenPayments.Field(description='Make Adyen Payment request.')
    adyen_payment_details = AdyenPaymentDetails.Field(description='Submit the Adyen Payment Details.')
