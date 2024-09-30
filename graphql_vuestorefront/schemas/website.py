# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import graphene
from graphene.types import generic
from odoo.addons.http_routing.models.ir_http import slugify
from odoo.addons.graphql_vuestorefront.schemas.objects import WebsiteMenu


class Homepage(graphene.Interface):
    meta_title = graphene.String()
    meta_keyword = graphene.String()
    meta_description = graphene.String()
    meta_image = graphene.String()
    meta_image_filename = graphene.String()
    json_ld = generic.GenericScalar()


class HomepageList(graphene.ObjectType):
    class Meta:
        interfaces = (Homepage,)


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
    website_homepage = graphene.Field(
        Homepage,
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

    @staticmethod
    def resolve_website_homepage(self, info):
        env = info.context['env']
        website = env['website'].get_current_website()

        return HomepageList(
            meta_title=website.website_meta_title,
            meta_keyword=website.website_meta_keywords,
            meta_description=website.website_meta_description,
            meta_image=f'/web/image/website/{website.id}/website_meta_img',
            meta_image_filename=slugify(website.website_meta_title),
            json_ld=website.json_ld,
        )
