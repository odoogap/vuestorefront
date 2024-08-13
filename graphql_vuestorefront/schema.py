# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_base import OdooObjectType
from odoo.addons.graphql_vuestorefront.schemas import (
    country, category, product, order,
    invoice, contact_us, user_profile, sign,
    address, wishlist, shop, payment,
    mailing_list, website, website_blog, website_page,
    website_cms,
)


class Query(
    OdooObjectType,
    country.CountryQuery,
    category.CategoryQuery,
    product.ProductQuery,
    order.OrderQuery,
    invoice.InvoiceQuery,
    user_profile.UserProfileQuery,
    address.AddressQuery,
    wishlist.WishlistQuery,
    shop.ShoppingCartQuery,
    payment.PaymentQuery,
    mailing_list.MailingContactQuery,
    mailing_list.MailingListQuery,
    website.WebsiteQuery,
    website_blog.BlogPostQuery,
    website_blog.BlogTagQuery,
    website_blog.BlogTagCategoryQuery,
    website_page.WebsitePageQuery,
    website_cms.CmsCollectionQuery,
    website_cms.CmsContentQuery,
):
    pass


class Mutation(
    OdooObjectType,
    contact_us.ContactUsMutation,
    user_profile.UserProfileMutation,
    sign.SignMutation,
    address.AddressMutation,
    wishlist.WishlistMutation,
    shop.ShopMutation,
    payment.PaymentMutation,
    payment.AdyenPaymentMutation,
    mailing_list.NewsletterSubscribeMutation,
    order.OrderMutation,
):
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[country.CountryList, category.CategoryList, product.ProductList, product.ProductVariantData, order.OrderList, order.ApplyGiftCardList,
           invoice.InvoiceList, wishlist.WishlistData, shop.CartData, mailing_list.MailingContactList,
           mailing_list.MailingListList, website_blog.BlogPostList, website_blog.BlogTagList,
           website_blog.BlogTagCategoryList, website_page.WebsitePageList, website_cms.CmsCollectionList,
           website_cms.CmsContentList]
)
