# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.http import request
from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum,
    WebsitePage,
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'id ASC'

    return sorting


class PageTypeEnum(graphene.Enum):
    Static = 'static'
    Products = 'products'


class WebsitePageFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    page_slug = graphene.String()
    page_type = graphene.List(PageTypeEnum)


class WebsitePageSortInput(graphene.InputObjectType):
    id = SortEnum()


class WebsitePages(graphene.Interface):
    website_pages = graphene.List(WebsitePage)
    total_count = graphene.Int(required=True)


class WebsitePageList(graphene.ObjectType):
    class Meta:
        interfaces = (WebsitePages,)


class WebsitePageQuery(graphene.ObjectType):
    website_page = graphene.Field(
        WebsitePage,
        id=graphene.Int(),
        page_slug=graphene.String(default_value=None),
    )
    website_pages = graphene.Field(
        WebsitePages,
        filter=graphene.Argument(WebsitePageFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(WebsitePageSortInput, default_value={})
    )

    @staticmethod
    def resolve_website_page(self, info, id=None, page_slug=None):
        env = info.context['env']
        WebsitePage = env['vsf.website.page'].sudo()
        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            website_page = WebsitePage.search(domain, limit=1)
        elif page_slug:
            domain += [('url', '=', page_slug)]
            website_page = WebsitePage.search(domain, limit=1)
        else:
            website_page = WebsitePage

        return website_page

    @staticmethod
    def resolve_website_pages(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = get_search_order(sort)
        domain = [('website_id', 'in', (False, website.id)), ('is_published', '=', True)]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        if filter.get('page_slug'):
            domain += [('url', '=', filter['page_slug'])]

        if filter.get('page_type'):
            page_types = [page_type.value for page_type in filter.get('page_type', [])]

            domain += [('page_type', 'in', page_types)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        WebsitePage = env['vsf.website.page'].sudo()
        total_count = WebsitePage.search_count(domain)
        website_pages = WebsitePage.search(domain, limit=page_size, offset=offset, order=order)
        return WebsitePageList(website_pages=website_pages, total_count=total_count)
