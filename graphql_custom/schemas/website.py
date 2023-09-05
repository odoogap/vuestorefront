# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.website import (
    WebsiteQuery as VSFWebsiteQuery,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomWebsiteMenu as WebsiteMenu,
)


class WebsiteQuery(VSFWebsiteQuery):
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
        res = VSFWebsiteQuery.resolve_website_menu(self, info)
        return res

    @staticmethod
    def resolve_website_mega_menu(self, info):
        res = VSFWebsiteQuery.resolve_website_mega_menu(self, info)
        return res

    @staticmethod
    def resolve_website_footer(self, info):
        res = VSFWebsiteQuery.resolve_website_footer(self, info)
        return res
