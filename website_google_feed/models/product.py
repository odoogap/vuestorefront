# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models
from odoo.addons.http_routing.models.ir_http import slug


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_google_feed_xml(self, website):
        domain = website.domain or ''
        if domain and domain[-1] == '/':
            domain = domain[:-1]

        feed_info_array = []

        for product in self:
            feed_info_array.append({
                'title': product.display_name,
                'link': "{}{}".format(domain, slug(product)),
                'description': product.description_sale,
                'image_link': '{}/web/image/product.product/{}/image'.format(domain, product.id),
                'price': '{} {}'.format(product.lst_price, product.currency_id.display_name),
                'product_type': ', '.join(product.public_categ_ids.mapped('display_name')),
                'condition': 'new',
                'id': product.id,
                # product.free_qty > 0
                'availability': 'in stock',
                'brand': self.env.user.company_id.display_name,
                'mpn': product.default_code,
                'adult': 'yes',
            })

        return feed_info_array
