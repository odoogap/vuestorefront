# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import datetime

from odoo import http, fields
from odoo.addons.website.controllers.main import Website
from odoo.http import request


class Website(Website):

    @http.route('/google-feed', type='http', auth="public", website=True, multilang=False)
    def google_feed(self, **kwargs):
        current_website = request.website
        Attachment = request.env['ir.attachment'].sudo()
        Product = request.env['product.product'].sudo()
        View = request.env['ir.ui.view'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        content = None

        def create_feed(url, content):
            return Attachment.create({
                'raw': content.encode(),
                'mimetype': mimetype,
                'type': 'binary',
                'name': url,
                'url': url,
            })

        dom = [('url', '=', '/google-feed-%d.xml' % current_website.id), ('type', '=', 'binary')]
        feed = Attachment.search(dom, limit=1)

        if feed:
            # Check if stored version is still valid
            create_date = fields.Datetime.from_string(feed.create_date)
            delta = datetime.datetime.now() - create_date
            if delta < datetime.timedelta(current_website.google_feed_expire_time):
                content = base64.b64decode(feed.datas)
            else:
                feed.unlink()

        if not content:
            product_domain = [('sale_ok', '=', True), ('website_published', '=', True)]
            products = Product.search(product_domain)
            feed_info_array = products.get_google_feed_xml(current_website)
            content = View._render_template('website_google_feed.feed_xml', {
                'website': current_website,
                'feed_info_array': feed_info_array,
            })

            create_feed('/google-feed-%d.xml' % current_website.id, content)

        return request.make_response(content, [('Content-Type', mimetype)])
