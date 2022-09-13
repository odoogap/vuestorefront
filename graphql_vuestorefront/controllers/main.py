# -*- coding: utf-8 -*-
# Copyright 2021 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import json
import werkzeug
from odoo import http
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.http import request, Response
from urllib.parse import urlparse

from ..schema import schema


class VSFAdyenController(AdyenController):

    # Deprecated
    @http.route(['/payment/adyen/return'], type='http', auth='public', csrf=False)
    def adyen_return(self, **post):
        # Confirm payment transaction
        super(VSFAdyenController, self).adyen_return(**post)

        tx_ids_list = request.session.get("__payment_tx_ids__", [])

        # If the session have tx_ids_list it means that the SO payment was done in Odoo
        if tx_ids_list:
            return werkzeug.utils.redirect('/payment/process')

        # If the Session not have Transactions Associated it means that the SO payment was done in VSF
        elif not tx_ids_list and post.get('merchantReference'):
            transaction_reference = post['merchantReference']

            payment_transaction = request.env['payment.transaction'].sudo().search([
                ('reference', 'like', str(transaction_reference))
            ])

            # Check the Order related with the transaction
            sale_order_ids = payment_transaction.sale_order_ids.ids
            sale_order = request.env['sale.order'].sudo().search([
                ('id', 'in', sale_order_ids), ('website_id', '!=', False)
            ], limit=1)

            # Get Website
            website = sale_order.website_id
            # Redirect to VSF
            vsf_payment_success_return_url = website.vsf_payment_success_return_url
            vsf_payment_error_return_url = website.vsf_payment_error_return_url

            request.session["__payment_tx_ids__"] = [payment_transaction.id]

            # Adyen Error Flow
            if post.get('authResult') and post['authResult'] == 'REFUSED':
                request.env['payment.transaction'].sudo().form_feedback(post, 'adyen')

                # Clear the payment_tx_ids
                request.session['__payment_tx_ids__'] = []

                return werkzeug.utils.redirect(vsf_payment_error_return_url)

            # Adyen Success Flow
            if post.get('authResult') not in ['CANCELLED']:
                request.env['payment.transaction'].sudo().form_feedback(post, 'adyen')

                # Confirm sale order
                PaymentProcessing().payment_status_poll()

                # Clear the payment_tx_ids
                request.session['__payment_tx_ids__'] = []

                return werkzeug.utils.redirect(vsf_payment_success_return_url)


class GraphQLController(http.Controller, GraphQLControllerMixin):

    def _set_website_context(self):
        """Set website context based on http_request_host header."""
        try:
            request_host = request.httprequest.headers.environ['HTTP_RESQUEST_HOST']
            website = request.env['website'].search([('domain', 'ilike', request_host)], limit=1)
            if website:
                context = dict(request.context)
                context.update({
                    'website_id': website.id,
                    'lang': website.default_lang_id.code,
                })
                request.context = context

                request_uid = http.request.env.uid
                website_uid = website.sudo().user_id.id

                if request_uid != website_uid \
                        and request.env['res.users'].sudo().browse(request_uid).has_group('base.group_public'):
                    request.uid = website_uid
        except:
            pass

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql/vsf", auth="user")
    def graphiql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphiql_request(schema.graphql_schema)

    # Optional monkey patch, needed to accept application/json GraphQL
    # requests. If you only need to accept GET requests or POST
    # with application/x-www-form-urlencoded content,
    # this is not necessary.
    GraphQLControllerMixin.patch_for_json("^/graphql/vsf/?$")

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.
    @http.route("/graphql/vsf", auth="public", csrf=False)
    def graphql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphql_request(schema.graphql_schema)

    @http.route('/vsf/categories', type='http', auth='public', csrf=False)
    def vsf_categories(self):
        self._set_website_context()
        website = request.env['website'].get_current_website()

        categories = []

        if website.default_lang_id:
            lang_code = website.default_lang_id.code
            domain = [('website_slug', '!=', False)]

            for category in request.env['product.public.category'].sudo().search(domain):
                category = category.with_context(lang=lang_code)
                categories.append(category.website_slug)

        return Response(
            json.dumps(categories),
            headers={'Content-Type': 'application/json'},
        )

    @http.route('/vsf/products', type='http', auth='public', csrf=False)
    def vsf_products(self):
        self._set_website_context()
        website = request.env['website'].get_current_website()

        products = []

        if website.default_lang_id:
            lang_code = website.default_lang_id.code
            domain = [('website_published', '=', True), ('website_slug', '!=', False)]

            for product in request.env['product.template'].sudo().search(domain):
                product = product.with_context(lang=lang_code)

                url_parsed = urlparse(product.website_slug)
                name = os.path.basename(url_parsed.path)
                path = product.website_slug.replace(name, '')

                products.append({
                    'name': name,
                    'path': '{}:slug'.format(path),
                })

        return Response(
            json.dumps(products),
            headers={'Content-Type': 'application/json'},
        )

    @http.route('/vsf/redirects', type='http', auth='public', csrf=False)
    def vsf_redirects(self):
        redirects = []

        for redirect in request.env['website.rewrite'].sudo().search([]):
            redirects.append({
                'from': redirect.url_from,
                'to': redirect.url_to,
            })

        return Response(
            json.dumps(redirects),
            headers={'Content-Type': 'application/json'},
        )
