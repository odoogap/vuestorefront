# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
import json

from odoo import _

from odoo.addons.payment import utils as payment_utils
from odoo.addons.website_sale.controllers.main import PaymentPortal
from odoo.addons.payment_stripe.controllers.main import StripeController


# -------------------------------- #
#           Stripe Payment          #
# -------------------------------- #

class StripeProviderInfoResult(graphene.ObjectType):
    stripe_provider_info = generic.GenericScalar()


class StripePaymentMethodsResult(graphene.ObjectType):
    stripe_payment_methods = generic.GenericScalar()


class StripeTransactionResult(graphene.ObjectType):
    transaction = generic.GenericScalar()


class StripePaymentsResult(graphene.ObjectType):
    stripe_payments = generic.GenericScalar()


class StripePaymentDetailsResult(graphene.ObjectType):
    stripe_payment_details = generic.GenericScalar()


class StripeProviderInfo(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)

    Output = StripeProviderInfoResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]
        website = env['website'].get_current_website()
        order = website.sale_get_order()

        payment_provider = PaymentProvider.search(domain, limit=1)
        if not payment_provider:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))
        
        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        stripe_provider_detail = payment_provider._stripe_get_inline_form_values(
            transaction.amount,
            transaction.currency_id,
            order.partner_id.id,
            True,
            sale_order_id=order.id
        )
        stripe_provider_info = json.loads(stripe_provider_detail)
        stripe_provider_info['payment_methods'] = payment_provider.payment_method_ids.mapped('code')
        return StripeProviderInfoResult(stripe_provider_info=stripe_provider_info)


class StripeTransaction(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)
        tokenization_requested = graphene.Boolean(default_value=False)

    Output = StripeTransactionResult

    @staticmethod
    def mutate(self, info, provider_id, tokenization_requested):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        website = env['website'].get_current_website()
        order = website.sale_get_order()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        payment_method_id = payment_provider_id.payment_method_ids[1].id if payment_provider_id.payment_method_ids else None
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))
        # Generate a new access token
        access_token = payment_utils.generate_access_token(order.partner_id.id, order.amount_total, order.currency_id.id)
        order.access_token = access_token
        transaction = PaymentPortal().shop_payment_transaction(
            order_id=order.id,
            access_token=order.access_token,
            provider_id=provider_id,
            payment_method_id=payment_method_id,
            token_id=None,
            amount=order.amount_total,
            flow='direct',
            tokenization_requested=tokenization_requested,
            landing_route='/shop/payment/validate',
        )

        transaction_id = PaymentTransaction.search([('reference', '=', transaction['reference'])], limit=1)

        # Update the field created_on_vsf
        transaction_id.created_on_vsf = True

        return StripeTransactionResult(transaction=transaction)


class StripePayments(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        payment_details = generic.GenericScalar(required=True, description='Return state.data')

    Output = StripePaymentsResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference, payment_details):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        PaymentTransaction = env['payment.transaction'].sudo()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider_id = PaymentProvider.search(domain, limit=1)
        if not payment_provider_id:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider_id.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))

        transaction = PaymentTransaction.search([('reference', '=', transaction_reference)], limit=1)
        if not transaction:
            raise GraphQLError(_('Payment transaction does not exist.'))

        payment_intent_id = payment_details.get("id")
        if payment_details.get('payment_intent'):
            payment_intent_id = payment_details.get("payment_intent")

        # Fetch the PaymentIntent and PaymentMethod objects from Stripe.
        payment_intent = transaction.provider_id._stripe_make_request(
            f'payment_intents/{payment_intent_id}',
            payload={'expand[]': 'payment_method'},  # Expand all required objects.
            method='GET',
        )
        StripeController._include_payment_intent_in_notification_data(payment_intent, payment_details)
        # Handle the notification data crafted with Stripe API's objects.
        transaction._handle_notification_data('stripe', payment_details)
        transaction._finalize_post_processing()
        return StripePaymentsResult(stripe_payments=payment_intent)


class StripePaymentMutation(graphene.ObjectType):
    stripe_provider_info = StripeProviderInfo.Field(description='Get Stripe Provider Info.')
    stripe_transaction = StripeTransaction.Field(description='Create Stripe Transaction')
    stripe_payments = StripePayments.Field(description='Make Stripe Payment request.')