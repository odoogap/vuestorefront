# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.order import (
    OrderFilterInput as VSFOrderFilterInput,
    OrderSortInput as VSFOrderSortInput,
    Orders as VSFOrders,
    OrderList as VSFOrderList,
    OrderQuery as VSFOrderQuery,
    ApplyCoupon as VSFApplyCoupon,
    ApplyGiftCard as VSFApplyGiftCard,
    OrderMutation as VSFOrderMutation,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomOrder as Order,
    CustomShippingMethod as ShippingMethod,
)


class Orders(VSFOrders):
    orders = graphene.List(Order)


class OrderList(VSFOrderList):
    class Meta:
        interfaces = (Orders,)


class OrderQuery(VSFOrderQuery):
    order = graphene.Field(
        Order,
        required=True,
        id=graphene.Int(),
    )
    orders = graphene.Field(
        Orders,
        filter=graphene.Argument(VSFOrderFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        sort=graphene.Argument(VSFOrderSortInput, default_value={})
    )
    delivery_methods = graphene.List(
        graphene.NonNull(ShippingMethod)
    )

    @staticmethod
    def resolve_order(self, info, id):
        res = VSFOrderQuery.resolve_order(self, info, id)
        return res

    @staticmethod
    def resolve_orders(self, info, filter, current_page, page_size, sort):
        res = VSFOrderQuery.resolve_orders(self, info, filter, current_page, page_size, sort)
        return OrderList(orders=res.orders and res.orders.sudo() or res.orders, total_count=res.total_count)

    @staticmethod
    def resolve_delivery_methods(self, info):
        """ Get all shipping/delivery methods """
        res = VSFOrderQuery.resolve_delivery_methods(self, info)
        return res


class ApplyCoupon(VSFApplyCoupon):
    class Arguments:
        promo = graphene.String()

    error = graphene.String()

    @staticmethod
    def mutate(self, info, promo):
        res = VSFApplyCoupon.mutate(self, info, promo)
        return res


class ApplyGiftCard(VSFApplyGiftCard):
    class Arguments:
        promo = graphene.String()

    error = graphene.String()

    @staticmethod
    def mutate(self, info, promo):
        res = VSFApplyGiftCard.mutate(self, info, promo)
        return res


class OrderMutation(VSFOrderMutation):
    apply_coupon = ApplyCoupon.Field(description='Apply Coupon')
    apply_gift_card = ApplyGiftCard.Field(description='Apply Gift Card')
