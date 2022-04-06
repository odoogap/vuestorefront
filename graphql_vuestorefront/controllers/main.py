# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import werkzeug
from odoo import http
from odoo.addons.web.controllers.main import Binary
from odoo.addons.graphql_base import GraphQLControllerMixin
# from odoo.addons.payment.controllers.portal import PaymentProcessing
# from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.http import request, Response
from odoo.tools.safe_eval import safe_eval

from ..schema import schema


class VSFBinary(Binary):
    @http.route(['/web/image',
                 '/web/image/<string:xmlid>',
                 '/web/image/<string:xmlid>/<string:filename>',
                 '/web/image/<string:xmlid>/<int:width>x<int:height>',
                 '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<string:model>/<int:id>/<string:field>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<int:id>',
                 '/web/image/<int:id>/<string:filename>',
                 '/web/image/<int:id>/<int:width>x<int:height>',
                 '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<int:id>-<string:unique>',
                 '/web/image/<int:id>-<string:unique>/<string:filename>',
                 '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
                 '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http',
                auth="public")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):
        """ Validate width and height against a whitelist """
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            resize_whitelist = safe_eval(ICP.get_param('vsf_image_resize_whitelist', '[]'))

            if resize_whitelist and width and height and \
                    (int(width) not in resize_whitelist or int(height) not in resize_whitelist):
                return request.not_found()
        except Exception:
            return request.not_found()

        return super(VSFBinary, self).content_image(
            xmlid=xmlid, model=model, id=id, field=field, filename_field=filename_field, unique=unique,
            filename=filename, mimetype=mimetype, download=download, width=width, height=height, crop=crop,
            access_token=access_token, **kwargs)


class VSFWebsite(http.Controller):

    @http.route('/vsf/redirects', type='http', auth='public', csrf=False)
    def vsf_redirects(self):
        redirects_list = []
        redirects = request.env['website.rewrite'].sudo().search([])
        if redirects:
            for redirect in redirects:
                redirect_dict = {'from': redirect.url_from, 'to': redirect.url_to}
                redirects_list.append(redirect_dict)
        result = json.dumps(redirects_list)
        return Response(result, headers={
            'Content-Type': 'application/json',
        })


# class VSFAdyenController(AdyenController):
#
#     @http.route(['/payment/adyen/return'], type='http', auth='public', csrf=False)
#     def adyen_return(self, **post):
#         # Confirm payment transaction
#         super(VSFAdyenController, self).adyen_return(**post)
#
#         tx_ids_list = request.session.get("__payment_tx_ids__", [])
#
#         # If the session have tx_ids_list it means that the SO payment was done in Odoo
#         if tx_ids_list:
#             return werkzeug.utils.redirect('/payment/process')
#
#         # If the Session not have Transactions Associated it means that the SO payment was done in VSF
#         elif not tx_ids_list and post.get('merchantReference'):
#             transaction_reference = post['merchantReference']
#
#             payment_transaction = request.env['payment.transaction'].sudo().search([
#                 ('reference', 'like', str(transaction_reference))
#             ])
#
#             sale_order_ids = payment_transaction.sale_order_ids.ids
#             sale_order = request.env['sale.order'].sudo().search([
#                 ('id', 'in', sale_order_ids), ('website_id', '!=', False)
#             ], limit=1)
#
#             # Get Website
#             website = sale_order.website_id
#             # Redirect to VSF
#             vsf_payment_return_url = website.vsf_payment_return_url
#
#             request.session["__payment_tx_ids__"] = [payment_transaction.id]
#
#             # Confirm sale order
#             PaymentProcessing().payment_status_poll()
#
#             # Clear the payment_tx_ids
#             request.session['__payment_tx_ids__'] = []
#
#             return werkzeug.utils.redirect(vsf_payment_return_url)


class GraphQLController(http.Controller, GraphQLControllerMixin):

    def get_domain_of_request_host(self):
        """ Trying get the http_request_host, to update the language that will be used """
        try:
            request_host = request.httprequest.headers.environ['HTTP_RESQUEST_HOST']

            domain = 'https://%s' % request_host

            website = request.env['website'].search([('domain', '=', domain)], limit=1)
            if website:
                context = dict(request.context)
                context.update({
                    'website_id': website.id,
                    'lang': website.default_lang_id.code,
                })
                request.context = context

                request_uid = http.request.env.uid
                website_uid = website.sudo().user_id.id

                if request_uid != website_uid and \
                        request.env['res.users'].sudo().browse(request_uid).has_group('base.group_public'):
                    request.uid = website_uid
        except:
            pass

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql/vsf", auth="user")
    def graphiql(self, **kwargs):
        self.get_domain_of_request_host()
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
        self.get_domain_of_request_host()
        return self._handle_graphql_request(schema.graphql_schema)
