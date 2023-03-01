# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum, Category
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'sequence ASC, id ASC'

    return sorting


class CategoryFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    parent = graphene.Boolean()


class CategorySortInput(graphene.InputObjectType):
    id = SortEnum()


class Categories(graphene.Interface):
    categories = graphene.List(Category)
    total_count = graphene.Int(required=True)


class CategoryList(graphene.ObjectType):
    class Meta:
        interfaces = (Categories,)


class CategoryQuery(graphene.ObjectType):
    category = graphene.Field(
        Category,
        id=graphene.Int(),
        slug=graphene.String(default_value=None),
    )
    categories = graphene.Field(
        Categories,
        filter=graphene.Argument(CategoryFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(CategorySortInput, default_value={})
    )

    @staticmethod
    def resolve_category(self, info, id=None, slug=None):
        env = info.context['env']
        Category = env['product.public.category']

        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            category = Category.search(domain, limit=1)
        elif slug:
            domain += [('website_slug', '=', slug)]
            category = Category.search(domain, limit=1)
        else:
            category = Category

        return category

    @staticmethod
    def resolve_categories(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = env['website'].get_current_website().website_domain()

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        # Parent if is a Top Category
        if filter.get('parent'):
            domain += [('parent_id', '=', False)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        ProductPublicCategory = env["product.public.category"]
        total_count = ProductPublicCategory.search_count(domain)
        categories = ProductPublicCategory.search(
            domain, limit=page_size, offset=offset, order=order)
        return CategoryList(categories=categories, total_count=total_count)
