# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.category import (
    CategoryFilterInput as VSFCategoryFilterInput,
    CategorySortInput as VSFCategorySortInput,
    Categories as VSFCategories,
    CategoryList as VSFCategoryList,
    CategoryQuery as VSFCategoryQuery,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaCategory as Category,
)


class Categories(VSFCategories):
    categories = graphene.List(Category)


class CategoryList(VSFCategoryList):
    class Meta:
        interfaces = (Categories,)


class CategoryQuery(VSFCategoryQuery):
    category = graphene.Field(
        Category,
        id=graphene.Int(),
        slug=graphene.String(default_value=None),
    )
    categories = graphene.Field(
        Categories,
        filter=graphene.Argument(VSFCategoryFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(VSFCategorySortInput, default_value={})
    )

    @staticmethod
    def resolve_category(self, info, id=None, slug=None):
        res = VSFCategoryQuery.resolve_category(self, info, id=id, slug=slug)
        return res

    @staticmethod
    def resolve_categories(self, info, filter, current_page, page_size, search, sort):
        res = VSFCategoryQuery.resolve_categories(self, info, filter, current_page, page_size, search, sort)
        return CategoryList(categories=res.categories, total_count=res.total_count)
