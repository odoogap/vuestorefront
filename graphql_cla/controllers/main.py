# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint

from odoo import http
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.http import request, Response

from ..schema import schema

_logger = logging.getLogger(__name__)


class GraphQLController(http.Controller, GraphQLControllerMixin):

    def _process_request(self, schema, data):
        # Set the vsf_debug_mode value that exist in the settings
        ICP = http.request.env['ir.config_parameter'].sudo()
        vsf_debug_mode = ICP.get_param('vsf_debug_mode', False)
        if vsf_debug_mode:
            try:
                request = http.request.httprequest
                _logger.info('# ------------------------------- GRAPHQL: DEBUG MODE -------------------------------- #')
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                          HEADERS                        #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', pprint.pformat(request.headers.environ))
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                     QUERY / MUTATION                    #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', data.get('query', None))
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                         ARGUMENTS                       #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', request.args.get('variables', None))
                _logger.info('')
                _logger.info('# ------------------------------------------------------------------------------------ #')
            except:
                pass
        return super(GraphQLController, self)._process_request(schema, data)

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

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.
    @http.route("/graphql/vsf", auth="public", csrf=False)
    def graphql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphql_request(schema.graphql_schema)
