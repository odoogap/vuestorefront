# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schema import (
    Query as VSFQuery,
    Mutation as VSFMutation,
)
from odoo.addons.graphql_custom.schemas import (
    address,
    category,
    contact_us,
    country,
    invoice,
    mailing_list,
    # product,
    # order,
    # wishlist,
    # shop,
    # store,
    # payment,
    # website,
    # website_page,
)


class Query(
    VSFQuery,
    address.AddressQuery,
    category.CategoryQuery,
    country.CountryQuery,
    invoice.InvoiceQuery,
    mailing_list.MailingContactQuery,
    mailing_list.MailingListQuery,
):
    pass


class Mutation(
    VSFMutation,
    address.AddressMutation,
    contact_us.ContactUsMutation,
    mailing_list.NewsletterSubscribeMutation,
):
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[category.CategoryList, country.CountryList, invoice.InvoiceList, mailing_list.MailingContactList,
           mailing_list.MailingListList]
)
