# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    product_tmpl_ids = fields.Many2many('product.template', relation='product_public_category_product_template_rel')

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
