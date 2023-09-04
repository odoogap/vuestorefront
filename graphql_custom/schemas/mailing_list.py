# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.mailing_list import (
    MailingContactFilterInput as VSFMailingContactFilterInput,
    MailingContactSortInput as VSFMailingContactSortInput,
    MailingContacts as VSFMailingContacts,
    MailingContactList as VSFMailingContactList,
    MailingContactQuery as VSFMailingContactQuery,
    MailingListFilterInput as VSFMailingListFilterInput,
    MailingListSortInput as VSFMailingListSortInput,
    MailingLists as VSFMailingLists,
    MailingListList as VSFMailingListList,
    MailingListQuery as VSFMailingListQuery,
    NewsletterSubscribe as VSFNewsletterSubscribe,
    MailingInput as VSFMailingInput,
    UserAddMultipleMailing as VSFUserAddMultipleMailing,
    NewsletterSubscribeMutation as VSFNewsletterSubscribeMutation,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomMailingContact as MailingContact,
    CustomMailingList as MailingList,
)


class MailingContacts(VSFMailingContacts):
    mailing_contacts = graphene.List(MailingContact)


class MailingContactList(VSFMailingContactList):
    class Meta:
        interfaces = (MailingContacts,)


class MailingContactQuery(VSFMailingContactQuery):
    mailing_contacts = graphene.Field(
        MailingContacts,
        filter=graphene.Argument(VSFMailingContactFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(VSFMailingContactSortInput, default_value={})
    )

    @staticmethod
    def resolve_mailing_contacts(self, info, filter, current_page, page_size, search, sort):
        res = VSFMailingContactQuery.resolve_mailing_contacts(self, info, filter, current_page, page_size, search, sort)
        return MailingContactList(mailing_contacts=res.mailing_contacts, total_count=res.total_count)


class MailingLists(VSFMailingLists):
    mailing_lists = graphene.List(MailingList)


class MailingListList(VSFMailingListList):
    class Meta:
        interfaces = (MailingLists,)


class MailingListQuery(VSFMailingListQuery):
    mailing_list = graphene.Field(
        MailingList,
        required=True,
        id=graphene.Int(),
    )
    mailing_lists = graphene.Field(
        MailingLists,
        filter=graphene.Argument(VSFMailingListFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(VSFMailingListSortInput, default_value={})
    )

    @staticmethod
    def resolve_mailing_list(self, info, id):
        res = VSFMailingListQuery.resolve_mailing_list(self, info, id)
        return res

    @staticmethod
    def resolve_mailing_lists(self, info, filter, current_page, page_size, search, sort):
        res = VSFMailingListQuery.resolve_mailing_lists(self, info, filter, current_page, page_size, search, sort)
        return MailingListList(mailing_lists=res.mailing_lists, total_count=res.total_count)


class NewsletterSubscribe(VSFNewsletterSubscribe):
    class Arguments:
        email = graphene.String()

    subscribed = graphene.Boolean()

    @staticmethod
    def mutate(self, info, email):
        res = VSFNewsletterSubscribe.mutate(self, info, email)
        return res


class UserAddMultipleMailing(VSFUserAddMultipleMailing):
    class Arguments:
        mailings = graphene.List(VSFMailingInput, default_value={}, required=True)

    Output = MailingContact

    @staticmethod
    def mutate(self, info, mailings):
        res = VSFUserAddMultipleMailing.mutate(self, info, mailings)
        return res


class NewsletterSubscribeMutation(VSFNewsletterSubscribeMutation):
    newsletter_subscribe = NewsletterSubscribe.Field(description='Subscribe to newsletter.')
    user_add_multiple_mailing = UserAddMultipleMailing.Field(
        description='Create or Update Multiple Mailing Contact information'
    )
