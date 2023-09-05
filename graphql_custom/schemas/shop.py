# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.shop import (
    Cart as VSFCart,
    CartData as VSFCartData,
    ShoppingCartQuery as VSFShoppingCartQuery,
    CartAddItem as VSFCartAddItem,
    CartUpdateItem as VSFCartUpdateItem,
    CartRemoveItem as VSFCartRemoveItem,
    CartClear as VSFCartClear,
    SetShippingMethod as VSFSetShippingMethod,
    ProductInput as VSFProductInput,
    CartLineInput as VSFCartLineInput,
    CartAddMultipleItems as VSFCartAddMultipleItems,
    CartUpdateMultipleItems as VSFCartUpdateMultipleItems,
    CartRemoveMultipleItems as VSFCartRemoveMultipleItems,
    CreateUpdatePartner as VSFCreateUpdatePartner,
    ShopMutation as VSFShopMutation,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomOrder as Order,
    CustomPartner as Partner,
)


class Cart(VSFCart):
    order = graphene.Field(Order)


class CartData(VSFCartData):
    class Meta:
        interfaces = (Cart,)


class ShoppingCartQuery(VSFShoppingCartQuery):
    cart = graphene.Field(
        Cart,
    )

    @staticmethod
    def resolve_cart(self, info):
        res = VSFShoppingCartQuery.resolve_cart(self, info)
        return CartData(order=res.order)


class CartAddItem(VSFCartAddItem):
    class Arguments:
        product_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, product_id, quantity):
        res = VSFCartAddItem.mutate(self, info, product_id, quantity)
        return CartData(order=res.order)


class CartUpdateItem(VSFCartUpdateItem):
    class Arguments:
        line_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, line_id, quantity):
        res = VSFCartUpdateItem.mutate(self, info, line_id, quantity)
        return CartData(order=res.order)


class CartRemoveItem(VSFCartRemoveItem):
    class Arguments:
        line_id = graphene.Int(required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, line_id):
        res = VSFCartRemoveItem.mutate(self, info, line_id)
        return CartData(order=res.order)


class CartClear(VSFCartClear):
    Output = Order

    @staticmethod
    def mutate(self, info):
        res = VSFCartClear.mutate(self, info)
        return res


class SetShippingMethod(VSFSetShippingMethod):
    class Arguments:
        shipping_method_id = graphene.Int(required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, shipping_method_id):
        res = VSFSetShippingMethod.mutate(self, info, shipping_method_id)
        return CartData(order=res.order)


# ---------------------------------------------------#
#      Additional Mutations that can be useful       #
# ---------------------------------------------------#

class CartAddMultipleItems(VSFCartAddMultipleItems):
    class Arguments:
        products = graphene.List(VSFProductInput, default_value={}, required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, products):
        res = VSFCartAddMultipleItems.mutate(self, info, products)
        return CartData(order=res.order)


class CartUpdateMultipleItems(VSFCartUpdateMultipleItems):
    class Arguments:
        lines = graphene.List(VSFCartLineInput, default_value={}, required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, lines):
        res = VSFCartUpdateMultipleItems.mutate(self, info, lines)
        return CartData(order=res.order)


class CartRemoveMultipleItems(VSFCartRemoveMultipleItems):
    class Arguments:
        line_ids = graphene.List(graphene.Int, required=True)

    Output = CartData

    @staticmethod
    def mutate(self, info, line_ids):
        res = VSFCartRemoveMultipleItems.mutate(self, info, line_ids)
        return CartData(order=res.order)


class CreateUpdatePartner(VSFCreateUpdatePartner):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        subscribe_newsletter = graphene.Boolean(required=True)

    Output = Partner

    @staticmethod
    def mutate(self, info, name, email, subscribe_newsletter):
        res = VSFCreateUpdatePartner.mutate(self, info, name, email, subscribe_newsletter)
        return res


class ShopMutation(VSFShopMutation):
    cart_add_item = CartAddItem.Field(description="Add Item")
    cart_update_item = CartUpdateItem.Field(description="Update Item")
    cart_remove_item = CartRemoveItem.Field(description="Remove Item")
    cart_clear = CartClear.Field(description="Cart Clear")
    cart_add_multiple_items = CartAddMultipleItems.Field(description="Add Multiple Items")
    cart_update_multiple_items = CartUpdateMultipleItems.Field(description="Update Multiple Items")
    cart_remove_multiple_items = CartRemoveMultipleItems.Field(description="Remove Multiple Items")
    set_shipping_method = SetShippingMethod.Field(description="Set Shipping Method on Cart")
    create_update_partner = CreateUpdatePartner.Field(description="Create or update a partner for guest checkout")
