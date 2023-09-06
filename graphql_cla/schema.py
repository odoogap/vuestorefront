# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schema import (
    Query as VSFQuery,
    Mutation as VSFMutation,
)
from odoo.addons.graphql_cla.schemas import (
    address,
    category,
    product,
    contact_us,
    country,
    invoice,
    mailing_list,
    order,
    shop,
    payment,
    sign,
    user_profile,
    wishlist,
    website,
)


class Query(
    VSFQuery,
    address.AddressQuery,
    category.CategoryQuery,
    product.ProductQuery,
    country.CountryQuery,
    invoice.InvoiceQuery,
    mailing_list.MailingContactQuery,
    mailing_list.MailingListQuery,
    order.OrderQuery,
    shop.ShoppingCartQuery,
    payment.PaymentQuery,
    user_profile.UserProfileQuery,
    wishlist.WishlistQuery,
    website.WebsiteQuery,
):
    pass


class Mutation(
    VSFMutation,
    address.AddressMutation,
    contact_us.ContactUsMutation,
    mailing_list.NewsletterSubscribeMutation,
    order.OrderMutation,
    shop.ShopMutation,
    payment.PaymentMutation,
    payment.AdyenPaymentMutation,
    sign.SignMutation,
    user_profile.UserProfileMutation,
    wishlist.WishlistMutation,
):
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[category.CategoryList, product.ProductList, product.ProductVariantData, country.CountryList,
           invoice.InvoiceList, mailing_list.MailingContactList, mailing_list.MailingListList, order.OrderList,
           shop.CartData, wishlist.WishlistData]
)
