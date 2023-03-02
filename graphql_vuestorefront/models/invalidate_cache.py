# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from datetime import datetime

import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class InvalidateCache(models.Model):
    _name = 'invalidate.cache'
    _description = 'VSF Invalidate Cache'

    res_model = fields.Char('Res Model', required=True, index=True)
    res_id = fields.Integer('Res ID', required=True)

    def init(self):
        super().init()
        self.env.cr.execute("""
            CREATE INDEX IF NOT EXISTS invalidate_cache_find_idx
            ON invalidate_cache(res_model, res_id);
        """)

    @api.model
    def find_invalidate_cache(self, res_model, res_id):
        cr = self.env.cr
        query = """
            SELECT id
            FROM invalidate_cache
            WHERE res_model=%s AND res_id=%s
            LIMIT 1;
        """
        params = (res_model, res_id,)

        cr.execute(query, params)
        return cr.fetchone()

    @api.model
    def create_invalidate_cache(self, res_model, res_ids):
        for res_id in res_ids:
            if not self.find_invalidate_cache(res_model, res_id):
                query = """
                    INSERT INTO invalidate_cache(res_model, res_id, create_date, write_date, create_uid, write_uid)
                    VALUES(%s, %s, %s, %s, %s, %s);
                """
                now = datetime.now()
                uid = self.env.user.id
                params = (res_model, res_id, now, now, uid, uid,)

                self.env.cr.execute(query, params)

    @api.model
    def delete_invalidate_cache(self, ids):
        if len(ids) == 1:
            ids = '({})'.format(ids[0])
        else:
            ids = tuple(ids)

        query = """
            DELETE FROM invalidate_cache
            WHERE id IN {};
        """.format(ids)

        self.env.cr.execute(query)

    @api.model
    def request_cache_invalidation(self, url, key, tags):
        if url and key and tags:
            try:
                requests.get(url, params={'key': key, 'tags': tags}, timeout=5)
            except Exception as e:
                _logger.error(e)
                self.env.cr.rollback()

    @api.model
    def request_vsf_cache_invalidation(self):
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('vsf_cache_invalidation_url', False)
        key = ICP.get_param('vsf_cache_invalidation_key', False)

        models = [
            {
                'name': 'product.template',
                'tags_method': '_get_product_tags',
            },
            {
                'name': 'product.public.category',
                'tags_method': '_get_category_tags',
            },
        ]

        for model in models:
            invalidate_caches = self.env['invalidate.cache'].search([('res_model', '=', model['name'])])
            if invalidate_caches:
                res_ids = invalidate_caches.mapped('res_id')
                tags = getattr(self, model['tags_method'])(res_ids)
                self.delete_invalidate_cache(invalidate_caches.ids)
                self.request_cache_invalidation(url, key, tags)
                self.env.cr.commit()

    def _get_product_tags(self, product_ids):
        tags = ','.join(f'P{product_id}' for product_id in product_ids)
        category_ids = self.env['product.template'].search(
            [('id', 'in', product_ids)]).mapped('public_categ_slug_ids').ids
        if category_ids:
            tags += ',' + ','.join(f'C{category_id}' for category_id in category_ids)
        return tags

    def _get_category_tags(self, product_ids):
        tags = ','.join(f'P{product_id}' for product_id in product_ids)
        category_ids = self.env['product.template'].search(
            [('id', 'in', product_ids)]).mapped('public_categ_slug_ids').ids
        if category_ids:
            tags += ',' + ','.join(f'C{category_id}' for category_id in category_ids)
        return tags
