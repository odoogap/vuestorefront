# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import WebsiteMenu


class WebsiteQuery(graphene.ObjectType):
    website_menu = graphene.List(
        graphene.NonNull(WebsiteMenu),
    )
    website_mega_menu = graphene.List(
        graphene.NonNull(WebsiteMenu),
    )
    website_footer = graphene.List(
        graphene.NonNull(WebsiteMenu),
    )

    @staticmethod
    def resolve_website_menu(self, info):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', False),
            ('is_mega_menu', '=', False),
        ]

        return env['website.menu'].search(domain)

    @staticmethod
    def resolve_website_mega_menu(self, info):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', False),
            ('is_mega_menu', '=', True),
        ]

        return env['website.menu'].search(domain)

    @staticmethod
    def resolve_website_footer(self, info):
        env = info.context['env']
        website = env['website'].get_current_website()

        domain = [
            ('website_id', '=', website.id),
            ('is_visible', '=', True),
            ('is_footer', '=', True),
            ('is_mega_menu', '=', False),
        ]

        return env['website.menu'].search(domain)
