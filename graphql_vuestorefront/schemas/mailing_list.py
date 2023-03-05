# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _
from odoo.addons.website_mass_mailing.controllers.main import MassMailController
from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum, MailingContact, MailingList
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    # Add id as last factor, so we can consistently get the same results
    if sorting:
        sorting += ', id ASC'
    else:
        sorting = 'id ASC'

    return sorting


# --------------------- #
#   Mailing Contacts    #
# --------------------- #

class MailingContactFilterInput(graphene.InputObjectType):
    id = graphene.Int()


class MailingContactSortInput(graphene.InputObjectType):
    id = SortEnum()


class MailingContacts(graphene.Interface):
    mailing_contacts = graphene.List(MailingContact)
    total_count = graphene.Int(required=True)


class MailingContactList(graphene.ObjectType):
    class Meta:
        interfaces = (MailingContacts,)


class MailingContactQuery(graphene.ObjectType):
    mailing_contacts = graphene.Field(
        MailingContacts,
        filter=graphene.Argument(MailingContactFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(MailingContactSortInput, default_value={})
    )

    @staticmethod
    def resolve_mailing_contacts(self, info, filter, current_page, page_size, search, sort):
        env = info.context['env']
        order = get_search_order(sort)

        domain = [('email', '=', env.user.email)]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id', False):
            domain += [('id', '=', filter['id'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        MailingContact = env['mailing.contact'].sudo()
        total_count = MailingContact.search_count(domain)
        mailing_contacts = MailingContact.search(domain, limit=page_size, offset=offset, order=order)
        return MailingContactList(mailing_contacts=mailing_contacts, total_count=total_count)


# --------------------- #
#     Mailing List      #
# --------------------- #

class MailingListFilterInput(graphene.InputObjectType):
    id = graphene.Int()


class MailingListSortInput(graphene.InputObjectType):
    id = SortEnum()


class MailingLists(graphene.Interface):
    mailing_lists = graphene.List(MailingList)
    total_count = graphene.Int(required=True)


class MailingListList(graphene.ObjectType):
    class Meta:
        interfaces = (MailingLists,)


class MailingListQuery(graphene.ObjectType):
    mailing_list = graphene.Field(
        MailingList,
        required=True,
        id=graphene.Int(),
    )
    mailing_lists = graphene.Field(
        MailingLists,
        filter=graphene.Argument(MailingListFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(MailingListSortInput, default_value={})
    )

    @staticmethod
    def resolve_mailing_list(self, info, id):
        return info.context['env']['mailing.list'].sudo().search([('id', '=', id), ('is_public', '=', True)], limit=1)

    @staticmethod
    def resolve_mailing_lists(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = [('is_public', '=', True)]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id', False):
            domain += [('id', '=', filter['id'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        MailingList = env["mailing.list"].sudo()
        total_count = MailingList.search_count(domain)
        mailing_lists = MailingList.search(domain, limit=page_size, offset=offset, order=order)
        return MailingListList(mailing_lists=mailing_lists, total_count=total_count)


class NewsletterSubscribe(graphene.Mutation):
    class Arguments:
        email = graphene.String()

    subscribed = graphene.Boolean()

    @staticmethod
    def mutate(self, info, email):
        env = info.context['env']
        website = env['website'].get_current_website()

        if website.vsf_mailing_list_id:
            MassMailController().subscribe(website.vsf_mailing_list_id.id, email, 'email')
            return NewsletterSubscribe(subscribed=True)

        return NewsletterSubscribe(subscribed=False)


class MailingInput(graphene.InputObjectType):
    mailinglistId = graphene.Int(required=True)
    optout = graphene.Boolean(required=True)


class UserAddMultipleMailing(graphene.Mutation):
    class Arguments:
        mailings = graphene.List(MailingInput, default_value={}, required=True)

    Output = MailingContact

    @staticmethod
    def mutate(self, info, mailings):
        env = info.context['env']
        user = request.env.user

        # Company name
        if user.partner_id.parent_id:
            company_name = user.partner_id.parent_id.name
        else:
            company_name = False

        # Country
        if user.partner_id.country_id:
            country_id = user.partner_id.country_id.id
        elif user.partner_id.parent_id:
            country_id = user.partner_id.parent_id.country_id.id
        else:
            country_id = False

        mailing_contact = env['mailing.contact'].sudo().search([('email', '=', user.email)], limit=1)

        for mailing in mailings:
            maillist_id = mailing['mailinglistId']
            optout = mailing['optout']

            mailing_list = env['mailing.list'].sudo().search([('id', '=', maillist_id)], limit=1)
            if not mailing_list:
                raise GraphQLError(_('Maillist does not exist.'))

            if mailing_contact:
                line = mailing_contact.subscription_list_ids.filtered(lambda mail: mail.list_id.id == maillist_id)

                if not mailing_contact.company_name or (company_name and mailing_contact.company_name != company_name):
                    mailing_contact.update({'company_name': company_name})

                if not mailing_contact.country_id or (country_id and mailing_contact.country_id != country_id):
                    mailing_contact.update({'country_id': country_id})

                if line:
                    line.update({'opt_out': optout})
                else:
                    mailing_contact.write(
                        {'subscription_list_ids': [(0, 0, {'list_id': mailing_list.id, 'opt_out': optout})], })
            else:
                mailing_contact = env['mailing.contact'].sudo().create({
                    'name': user.name,
                    'country_id': country_id,
                    'email': user.email,
                    'company_name': company_name,
                    'subscription_list_ids': [(0, 0, {'list_id': mailing_list.id, 'opt_out': optout})],
                })

        return mailing_contact


class NewsletterSubscribeMutation(graphene.ObjectType):
    newsletter_subscribe = NewsletterSubscribe.Field(description='Subscribe to newsletter.')
    user_add_multiple_mailing = UserAddMultipleMailing.Field(
        description='Create or Update Multiple Mailing Contact information')
