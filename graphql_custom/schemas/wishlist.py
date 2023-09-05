# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.wishlist import (
    WishlistItems as VSFWishlistItems,
    WishlistData as VSFWishlistData,
    WishlistQuery as VSFWishlistQuery,
    WishlistAddItem as VSFWishlistAddItem,
    WishlistRemoveItem as VSFWishlistRemoveItem,
    WishlistMutation as VSFWishlistMutation,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomWishlistItem as WishlistItem,
)


class WishlistItems(VSFWishlistItems):
    wishlist_items = graphene.List(WishlistItem)


class WishlistData(VSFWishlistData):
    class Meta:
        interfaces = (WishlistItems,)


class WishlistQuery(VSFWishlistQuery):
    wishlist_items = graphene.Field(
        WishlistData,
    )

    @staticmethod
    def resolve_wishlist_items(root, info):
        """ Get current user wishlist items """
        res = VSFWishlistQuery.resolve_wishlist_items(root, info)
        return WishlistData(wishlist_items=res.wishlist_items, total_count=res.total_count)


class WishlistAddItem(VSFWishlistAddItem):
    class Arguments:
        product_id = graphene.Int(required=True)

    Output = WishlistData

    @staticmethod
    def mutate(self, info, product_id):
        res = VSFWishlistAddItem.mutate(self, info, product_id)
        return WishlistData(wishlist_items=res.wishlist_items, total_count=res.total_count)


class WishlistRemoveItem(VSFWishlistRemoveItem):
    class Arguments:
       wish_id = graphene.Int(required=True)

    Output = WishlistData

    @staticmethod
    def mutate(self, info, wish_id):
        res = VSFWishlistRemoveItem.mutate(self, info, wish_id)
        return WishlistData(wishlist_items=res.wishlist_items, total_count=res.total_count)


class WishlistMutation(VSFWishlistMutation):
    wishlist_add_item = WishlistAddItem.Field(description="Add Item")
    wishlist_remove_item = WishlistRemoveItem.Field(description="Remove Item")
