# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.graphql_vuestorefront.controllers.main import GraphQLController
from odoo.addons.graphql_vuestorefront_extend_demo.schema_models import *

import logging

_logger = logging.getLogger(__name__)


class YourGraphQLController(GraphQLController):

    def graphiql(self, **kwargs):
        super().graphiql(**kwargs)
        module_name = __name__.split('.')[2]
        self._check_load_schema(module_name)
        return self._handle_graphiql_request(self._schema.graphql_schema)

    def graphql(self, **kwargs):
        super().graphql(**kwargs)
        module_name = __name__.split('.')[2]
        self._check_load_schema(module_name)
        return self._handle_graphql_request(self._schema.graphql_schema)
