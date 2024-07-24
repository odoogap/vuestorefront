# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import WebsiteMenu


class WebsiteQuery(graphene.ObjectType):
    website_menu = graphene.List(
        graphene.NonNull(WebsiteMenu),
        no_parent=graphene.Boolean(),
    )
    website_mega_menu = graphene.List(
        graphene.NonNull(WebsiteMenu),
        no_parent=graphene.Boolean(),
    )
    website_footer = graphene.List(
        graphene.NonNull(WebsiteMenu),
        no_parent=graphene.Boolean(),
    )

    @staticmethod
    def resolve_website_menu(self, info, no_parent=False):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', False),
            ('is_mega_menu', '=', False),
        ]

        if no_parent:
            domain += [('parent_id', '=', False)]

        return env['website.menu'].search(domain)

    @staticmethod
    def resolve_website_mega_menu(self, info, no_parent=False):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', False),
            ('is_mega_menu', '=', True),
        ]

        if no_parent:
            domain += [('parent_id', '=', False)]

        return env['website.menu'].search(domain)

    @staticmethod
    def resolve_website_footer(self, info, no_parent=False):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', True),
            ('is_mega_menu', '=', False),
        ]

        if no_parent:
            domain += [('parent_id', '=', False)]

        return env['website.menu'].search(domain)
