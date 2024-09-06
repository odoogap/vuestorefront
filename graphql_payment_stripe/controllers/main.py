# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.graphql_vuestorefront.controllers.main import GraphQLController as VSFGraphQLController

from ..schema import schema


class GraphQLController(VSFGraphQLController):
    @http.route(auth="public")
    def graphiql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphiql_request(schema.graphql_schema)

    @http.route()
    def graphql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphql_request(schema.graphql_schema)