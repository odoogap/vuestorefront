# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _
from odoo.osv import expression

from odoo.addons.graphql_vuestorefront.schemas.product import (
    Products as VSFProducts,
    ProductList as VSFProductList,
    ProductFilterInput as VSFProductFilterInput,
    ProductSortInput as VSFProductSortInput,
    ProductVariant as VSFProductVariant,
    ProductVariantData as VSFProductVariantData,
    ProductQuery as VSFProductQuery,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomProduct as Product,
    CustomAttribute as Attribute,
    CustomAttributeValue as AttributeValue,
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        if field == 'price':
            sorting += 'list_price %s' % val.value
        else:
            sorting += '%s %s' % (field, val.value)

    # Add id as last factor, so we can consistently get the same results
    if sorting:
        sorting += ', id ASC'
    else:
        sorting = 'id ASC'

    return sorting


def get_search_domain(env, search, **kwargs):
    # Only get published products
    domains = [env['website'].get_current_website().sale_product_domain()]

    # Filter with ids
    if kwargs.get('ids', False):
        domains.append([('id', 'in', kwargs['ids'])])

    # Filter with Category ID
    if kwargs.get('category_id', False):
        domains.append([('public_categ_ids', 'child_of', kwargs['category_id'])])

    # Filter with Category Slug
    if kwargs.get('category_slug', False):
        domains.append([('public_categ_slug_ids.website_slug', '=', kwargs['category_slug'])])

    # Filter With Name
    if kwargs.get('name', False):
        name = kwargs['name']
        for n in name.split(" "):
            domains.append([('name', 'ilike', n)])

    if search:
        for srch in search.split(" "):
            domains.append([
                '|', '|', ('name', 'ilike', srch), ('description_sale', 'like', srch), ('default_code', 'like', srch)])

    partial_domain = domains.copy()

    # Product Price Filter
    if kwargs.get('min_price', False):
        domains.append([('list_price', '>=', float(kwargs['min_price']))])
    if kwargs.get('max_price', False):
        domains.append([('list_price', '<=', float(kwargs['max_price']))])

    # Deprecated: filter with Attribute Value
    if kwargs.get('attribute_value_id', False):
        domains.append([('attribute_line_ids.value_ids', 'in', kwargs['attribute_value_id'])])

    # Filter with Attribute Value
    if kwargs.get('attrib_values', False):
        attributes = {}
        attributes_domain = []

        for value in kwargs['attrib_values']:
            try:
                value = value.split('-')
                if len(value) != 2:
                    continue

                attribute_id = int(value[0])
                attribute_value_id = int(value[1])
            except ValueError:
                continue

            if attribute_id not in attributes:
                attributes[attribute_id] = []

            attributes[attribute_id].append(attribute_value_id)

        for key, value in attributes.items():
            attributes_domain.append([('attribute_line_ids.value_ids', 'in', value)])

        attributes_domain = expression.AND(attributes_domain)
        domains.append(attributes_domain)

    return expression.AND(domains), expression.AND(partial_domain)


def get_product_list(env, current_page, page_size, search, sort, **kwargs):
    Product = env['product.template'].sudo()
    domain, partial_domain = get_search_domain(env, search, **kwargs)

    # First offset is 0 but first page is 1
    if current_page > 1:
        offset = (current_page - 1) * page_size
    else:
        offset = 0
    order = get_search_order(sort)
    products = Product.search(domain, order=order)

    # If attribute values are selected, we need to get the full list of attribute values and prices
    if domain == partial_domain:
        attribute_values = products.mapped('variant_attribute_value_ids')
        prices = products.mapped('list_price')
    else:
        without_attributes_products = Product.search(partial_domain)
        attribute_values = without_attributes_products.mapped('variant_attribute_value_ids')
        prices = without_attributes_products.mapped('list_price')

    total_count = len(products)
    products = products[offset:offset + page_size]
    if prices:
        return products, total_count, attribute_values, min(prices), max(prices)
    return products, total_count, attribute_values, 0.0, 0.0


class Products(VSFProducts):
    products = graphene.List(Product)
    attribute_values = graphene.List(AttributeValue)


class ProductList(VSFProductList):
    class Meta:
        interfaces = (Products,)


class ProductVariant(VSFProductVariant):
    product = graphene.Field(Product)


class ProductVariantData(VSFProductVariantData):
    class Meta:
        interfaces = (ProductVariant,)


class ProductQuery(VSFProductQuery):
    product = graphene.Field(
        Product,
        id=graphene.Int(default_value=None),
        slug=graphene.String(default_value=None),
        barcode=graphene.String(default_value=None),
    )
    products = graphene.Field(
        Products,
        filter=graphene.Argument(VSFProductFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(VSFProductSortInput, default_value={})
    )
    attribute = graphene.Field(
        Attribute,
        required=True,
        id=graphene.Int(),
    )
    product_variant = graphene.Field(
        ProductVariant,
        required=True,
        product_template_id=graphene.Int(),
        combination_id=graphene.List(graphene.Int)
    )

    @staticmethod
    def resolve_product(self, info, id=None, slug=None, barcode=None):
        res = VSFProductQuery.resolve_product(self, info, id=id, slug=slug, barcode=barcode)
        return res

    @staticmethod
    def resolve_products(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        products, total_count, attribute_values, min_price, max_price = get_product_list(
            env, current_page, page_size, search, sort, **filter)
        return ProductList(products=products, total_count=total_count, attribute_values=attribute_values,
                           min_price=min_price, max_price=max_price)

    @staticmethod
    def resolve_attribute(self, info, id):
        res = VSFProductQuery.resolve_attribute(self, info, id)
        return res

    @staticmethod
    def resolve_product_variant(self, info, product_template_id, combination_id):
        env = info.context["env"]

        website = env['website'].get_current_website()
        request.website = website
        pricelist = website.get_current_pricelist()

        product_template = env['product.template'].browse(product_template_id)
        combination = env['product.template.attribute.value'].browse(combination_id)

        variant_info = product_template._get_combination_info(combination, pricelist)

        product = env['product.product'].browse(variant_info['product_id'])

        # Condition to verify if Product exist
        if not product:
            raise GraphQLError(_('Product does not exist'))

        is_combination_possible = product_template._is_combination_possible(combination)

        # Condition to Verify if Product is active or if combination exist
        if not product.active or not is_combination_possible:
            variant_info['is_combination_possible'] = False
        else:
            variant_info['is_combination_possible'] = True

        return ProductVariantData(
            product=product,
            product_template_id=variant_info['product_template_id'],
            display_name=variant_info['display_name'],
            display_image=variant_info['display_image'],
            price=variant_info['price'],
            list_price=variant_info['list_price'],
            has_discounted_price=variant_info['has_discounted_price'],
            is_combination_possible=variant_info['is_combination_possible']
        )
