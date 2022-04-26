# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _
from odoo.http import request
from odoo.osv import expression

from odoo.addons.graphql_vuestorefront.schemas.objects import PaymentAcquirer
from odoo.addons.graphql_vuestorefront.schemas.shop import Cart, CartData
from odoo.addons.website_sale.controllers.main import PaymentPortal


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

    def resolve_payment_acquirer(self, info, id):
        domain = [
            ('id', '=', id),
            ('state', 'in', ['enabled', 'test']),
        ]
        payment_acquirer = info.context["env"]['payment.acquirer'].sudo().search(domain, limit=1)
        if not payment_acquirer:
            raise GraphQLError(_('Payment acquirer does not exist.'))
        return payment_acquirer

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
        return env['payment.acquirer'].search(domain)

    def resolve_payment_confirmation(self, info):
        env = info.context["env"]

        PaymentTransaction = env['payment.transaction']
        Order = env['sale.order']

        # Pass in the session the sale_order created in vsf
        payment_transaction_id = request.session.get('__payment_monitored_tx_ids__')

        if payment_transaction_id and payment_transaction_id[0]:

            payment_transaction = PaymentTransaction.sudo().search([
                ('id', '=', payment_transaction_id[0])], limit=1)

            sale_order_id = payment_transaction.sale_order_ids.ids[0]

        if not sale_order_id:
            raise GraphQLError(_('Cart does not exist'))

        order = Order.sudo().search([('id', '=', sale_order_id)], limit=1)

        if order.exists():
            return CartData(order=order)


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


class PaymentMutation(graphene.ObjectType):
    make_payment = MakePayment.Field(description='Creates a new payment request.')
