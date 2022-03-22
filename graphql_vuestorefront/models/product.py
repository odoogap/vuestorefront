# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from odoo import models, fields, api, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        self._set_vsf_tags()
        return res

    def unlink(self):
        self._set_vsf_tags()
        return super(ProductTemplate, self).unlink()

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        """ Add discount value and percentage based """
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        discount = 0
        discount_perc = 0

        if combination_info['has_discounted_price']:
            discount = combination_info['list_price'] - combination_info['price']
            discount_perc = discount * 100 / combination_info['list_price']

        combination_info.update({
            'discount': round(discount, 2),
            'discount_perc': round(discount_perc, 2),
        })

        return combination_info


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

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
                    mapped('product_template_attribute_value_ids').
                    mapped('product_attribute_value_id').ids)]

    attribute_value_ids = fields.Many2many('product.attribute.value', readonly=True)

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

    def write(self, vals):
        res = super(ProductPublicCategory, self).write(vals)
        self._set_vsf_tags()
        return res

    def unlink(self):
        self._set_vsf_tags()
        return super(ProductPublicCategory, self).unlink()
