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
from odoo.addons.payment_stripe.const import API_VERSION, PROXY_URL

# --------------------------------- #
#           Stripe Payment          #
# --------------------------------- #

class StripeProviderInfoResult(graphene.ObjectType):
    stripe_provider_info = generic.GenericScalar()


class StripeTransactionResult(graphene.ObjectType):
    transaction = generic.GenericScalar()


class StripeGetInlineFormValuesResult(graphene.ObjectType):
    stripe_get_inline_form_values = generic.GenericScalar()


class StripeProviderInfo(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = StripeProviderInfoResult

    @staticmethod
    def mutate(self, info, provider_id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider = PaymentProvider.search(domain, limit=1)
        if not payment_provider:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))

        stripe_provider_info = {
            'state': payment_provider.state,
            'publishable_key': payment_provider.stripe_publishable_key,
            'api_version': API_VERSION,
            'proxy_url': PROXY_URL
        }

        return StripeProviderInfoResult(stripe_provider_info=stripe_provider_info)


class StripeGetInlineFormValues(graphene.Mutation):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = StripeGetInlineFormValuesResult

    @staticmethod
    def mutate(self, info, provider_id):
        env = info.context["env"]
        PaymentProvider = env['payment.provider'].sudo()
        website = env['website'].get_current_website()
        order = website.sale_get_order()
        domain = [
            ('id', '=', provider_id),
            ('state', 'in', ['enabled', 'test']),
        ]

        payment_provider = PaymentProvider.search(domain, limit=1)
        if not payment_provider:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))

        stripe_get_inline_form_values = payment_provider._stripe_get_inline_form_values(
            amount=order.amount_total,
            currency=order.currency_id,
            partner_id=order.partner_id.id,
            is_validation=True,
            sale_order_id=order.id
        )
        stripe_get_inline_form_values = json.loads(stripe_get_inline_form_values)
        stripe_get_inline_form_values['payment_methods'] = payment_provider.payment_method_ids.mapped('code')
        return StripeGetInlineFormValuesResult(stripe_get_inline_form_values=stripe_get_inline_form_values)


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

        payment_provider = PaymentProvider.search(domain, limit=1)
        payment_method = payment_provider.payment_method_ids[0] if payment_provider.payment_method_ids else None

        if not payment_method:
            raise GraphQLError(_('Payment Method does not exist.'))

        if not payment_provider:
            raise GraphQLError(_('Payment Provider does not exist.'))

        if not payment_provider.code == 'stripe':
            raise GraphQLError(_('Payment Provider "Stripe" does not exist.'))

        # Generate a new access token
        access_token = payment_utils.generate_access_token(order.partner_id.id, order.amount_total, order.currency_id.id)
        order.access_token = access_token

        transaction = PaymentPortal().shop_payment_transaction(
            order_id=order.id,
            access_token=order.access_token,
            provider_id=provider_id,
            payment_method_id=payment_method.id,
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


class StripePaymentMutation(graphene.ObjectType):
    stripe_provider_info = StripeProviderInfo.Field(description='Get Stripe Provider Info.')
    stripe_get_inline_form_values = StripeGetInlineFormValues.Field(description='Get Stripe Inline Form Values')
    stripe_transaction = StripeTransaction.Field(description='Create Stripe Transaction')
