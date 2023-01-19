# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum,
    CmsCollection,
    CmsContent
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


# --------------------------------- #
#          Cms Collections          #
# --------------------------------- #

class CmsCollectionFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    website_slug = graphene.String()


class CmsCollectionSortInput(graphene.InputObjectType):
    id = SortEnum()


class CmsCollections(graphene.Interface):
    cms_collections = graphene.List(CmsCollection)
    total_count = graphene.Int(required=True)


class CmsCollectionList(graphene.ObjectType):
    class Meta:
        interfaces = (CmsCollections,)


class CmsCollectionQuery(graphene.ObjectType):
    cms_collection = graphene.Field(
        CmsCollection,
        id=graphene.Int(),
        website_slug=graphene.String(default_value=None),
    )
    cms_collections = graphene.Field(
        CmsCollections,
        filter=graphene.Argument(CmsCollectionFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(CmsCollectionSortInput, default_value={})
    )

    @staticmethod
    def resolve_cms_collection(self, info, id=None, website_slug=None):
        env = info.context['env']
        CmsCollection = env['cms.collection'].sudo()
        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            cms_collection = CmsCollection.search(domain, limit=1)
        elif website_slug:
            domain += [('website_slug', '=', website_slug)]
            cms_collection = CmsCollection.search(domain, limit=1)
        else:
            cms_collection = CmsCollection

        return cms_collection

    @staticmethod
    def resolve_cms_collections(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = env['website'].get_current_website().website_domain()

        if search:
            for srch in search.split(" "):
                domain += ['|', ('name', 'ilike', srch), ('subtitle', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        if filter.get('website_slug'):
            domain += [('website_slug', '=', filter['website_slug'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        CmsCollection = env['cms.collection'].sudo()
        total_count = CmsCollection.search_count(domain)
        cms_collections = CmsCollection.search(domain, limit=page_size, offset=offset, order=order)
        return CmsCollectionList(cms_collections=cms_collections, total_count=total_count)


# --------------------------------- #
#            Cms Contents           #
# --------------------------------- #

class CmsContentFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    website_slug = graphene.String()


class CmsContentSortInput(graphene.InputObjectType):
    id = SortEnum()


class CmsContents(graphene.Interface):
    cms_contents = graphene.List(CmsContent)
    total_count = graphene.Int(required=True)


class CmsContentList(graphene.ObjectType):
    class Meta:
        interfaces = (CmsContents,)


class CmsContentQuery(graphene.ObjectType):
    cms_content = graphene.Field(
        CmsContent,
        id=graphene.Int(),
        website_slug=graphene.String(default_value=None),
    )
    cms_contents = graphene.Field(
        CmsContents,
        filter=graphene.Argument(CmsContentFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(CmsContentSortInput, default_value={})
    )

    @staticmethod
    def resolve_cms_content(self, info, id=None, website_slug=None):
        env = info.context['env']
        CmsContent = env['cms.content'].sudo()
        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            cms_content = CmsContent.search(domain, limit=1)
        elif website_slug:
            domain += [('website_slug', '=', website_slug)]
            cms_content = CmsContent.search(domain, limit=1)
        else:
            cms_content = CmsContent

        return cms_content

    @staticmethod
    def resolve_cms_contents(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = env['website'].get_current_website().website_domain()
        domain += [('is_published', '=', True)]

        if search:
            for srch in search.split(" "):
                domain += ['|', '|', ('name', 'ilike', srch), ('subtitle', 'ilike', srch),
                           ('website_meta_keywords', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        if filter.get('website_slug'):
            domain += [('website_slug', '=', filter['website_slug'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        CmsContent = env['cms.content'].sudo()
        total_count = CmsContent.search_count(domain)
        cms_contents = CmsContent.search(domain, limit=page_size, offset=offset, order=order)
        return CmsContentList(cms_contents=cms_contents, total_count=total_count)
