# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _

from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.addons.graphql_vuestorefront.schemas.objects import WishlistItem


class WishlistItems(graphene.Interface):
    wishlist_items = graphene.List(WishlistItem)
    total_count = graphene.Int(required=True)


class WishlistData(graphene.ObjectType):
    class Meta:
        interfaces = (WishlistItems,)


class WishlistQuery(graphene.ObjectType):
    wishlist_items = graphene.Field(
        WishlistData,
    )

    @staticmethod
    def resolve_wishlist_items(root, info):
        """ Get current user wishlist items """
        env = info.context['env']
        website = env['website'].get_current_website()
        request.website = website
        wishlist_items = env['product.wishlist'].current()
        total_count = len(wishlist_items)
        return WishlistData(wishlist_items=wishlist_items, total_count=total_count)


class WishlistAddItem(graphene.Mutation):
    class Arguments:
        product_id = graphene.Int(required=True)

    Output = WishlistData

    @staticmethod
    def mutate(self, info, product_id):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website

        values = env['product.wishlist'].with_context(display_default_code=False).current()
        if values.filtered(lambda v: v.product_id.id == product_id):
            raise GraphQLError(_('Product already exists in the Wishlist.'))

        WebsiteSaleWishlist().add_to_wishlist(product_id)

        wishlist_items = env['product.wishlist'].current()
        total_count = len(wishlist_items)
        return WishlistData(wishlist_items=wishlist_items, total_count=total_count)


class WishlistRemoveItem(graphene.Mutation):
    class Arguments:
       wish_id = graphene.Int(required=True)

    Output = WishlistData

    @staticmethod
    def mutate(self, info, wish_id):
        env = info.context['env']
        Wishlist = env['product.wishlist'].sudo()

        wish_id = Wishlist.search([('id', '=', wish_id)], limit=1)
        wish_id.unlink()

        website = env['website'].get_current_website()
        request.website = website
        wishlist_items = env['product.wishlist'].current()

        total_count = len(wishlist_items)
        return WishlistData(wishlist_items=wishlist_items, total_count=total_count)


class WishlistMutation(graphene.ObjectType):
    wishlist_add_item = WishlistAddItem.Field(description="Add Item")
    wishlist_remove_item = WishlistRemoveItem.Field(description="Remove Item")
