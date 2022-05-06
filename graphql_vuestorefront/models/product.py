# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from odoo import models, fields, api, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    slug = fields.Char('Slug')
    public_categ_ids = fields.Many2many(
        'product.public.category', relation='product_public_category_product_template_rel',
        string='Website Product Category',
        help="Categories can be published on the Shop page (online catalog grid) to help "
             "customers find all the items within a category. To publish them, go to the Shop page, "
             "hit Customize and turn *Product Categories* on. A product can belong to several categories.")

    @api.multi
    def _is_in_wishlist(self):
        self.ensure_one()
        return self in self.env['product.wishlist'].current().mapped('product_id.product_tmpl_id')

    def _set_vsf_tags(self):
        for product in self:
            tags = []
            product_tag = 'P%s' % product.id
            tags.append(product_tag)
            category_ids = product.public_categ_ids.ids
            for category_id in category_ids:
                tags.append('C%s' % category_id)
            product._vsf_request_cache_invalidation(tags)

    def _vsf_request_cache_invalidation(self, tags_list):
        url = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_url')
        key = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_key')
        tags = tags_list

        # Make the GET request to the /cache-invalidate
        requests.get(url, params={'key': key, 'tag': tags})

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        self._set_vsf_tags()
        return res

    @api.multi
    def unlink(self):
        self._set_vsf_tags()
        return super(ProductTemplate, self).unlink()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _is_in_wishlist(self):
        self.ensure_one()
        return self in self.env['product.wishlist'].current().mapped('product_id')

    def _get_combination_info_variant(self, pricelist=False, add_qty=1):
        context = dict(self.env.context, quantity=add_qty, pricelist=pricelist.id if pricelist else False)
        product = self.with_context(context)
        product_template = self.product_tmpl_id
        list_price = product.price_compute('list_price')[self.id]
        price = product.price if pricelist else list_price
        price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
        has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount,
                                                                                           price) == 1
        discount = list_price - price
        discount_perc = discount * 100 / list_price

        return {
            'product_id': product.id,
            'product_template_id': product_template.id,
            'display_name': product.display_name,
            'display_image': bool(product.image),
            'price': price,
            'list_price': list_price,
            'price_extra': product.price_extra,
            'has_discounted_price': has_discounted_price,
            'discount': round(discount, 2),
            'discount_perc': round(discount_perc, 2),
        }


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    product_tmpl_ids = fields.Many2many('product.template', relation='product_public_category_product_template_rel')
    attribute_value_ids = fields.Many2many('product.attribute.value', readonly=True)
    slug = fields.Char('Slug')

    @api.model
    def _update_website_filtering(self):
        """
        Filtering attribute values on the website should be based on the ecommerce categories.
        For each category, this method computes a list of attribute values from variants of published products.
        This will ensure that the available attribute values on the website filtering will return results.
        By default, Odoo only shows attributes that will return results but doesn't consider that a particular
        attribute value may not have a variant.
        """
        ProductTemplate = self.env['product.template']

        for category in self.env['product.public.category'].search([]):
            products = ProductTemplate.search([
                ('public_categ_ids', 'child_of', category.id), ('website_published', '=', True)])

            category.attribute_value_ids = [
                (6, 0, products.
                 mapped('product_variant_ids').
                 mapped('attribute_value_ids').ids)
            ]

    def _set_vsf_tags(self):
        for category in self:
            tags = 'C%s' % category.id
            category._vsf_request_cache_invalidation(tags)

    def _vsf_request_cache_invalidation(self, tags_list):
        url = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_url')
        key = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_key')
        tags = tags_list

        # Make the GET request to the /cache-invalidate
        requests.get(url, params={'key': key, 'tag': tags})

    @api.multi
    def write(self, vals):
        res = super(ProductPublicCategory, self).write(vals)
        self._set_vsf_tags()
        return res

    @api.multi
    def unlink(self):
        self._set_vsf_tags()
        return super(ProductPublicCategory, self).unlink()


class ProductAttributevalue(models.Model):
    _inherit = "product.attribute.value"

    display_type = fields.Selection(related='attribute_id.type')