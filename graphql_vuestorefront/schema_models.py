# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import graphene
from odoo.addons.graphql_base import OdooObjectType
import logging

_logger = logging.getLogger(__name__)


# base types


class GraphQLType(OdooObjectType):
    _odoo_model = False


class GraphQLQuery(graphene.ObjectType):
    _odoo_model = False


# dynamic types


class LinkTracker(GraphQLType):
    _odoo_model = "link.tracker"


class LinkTrackerQuery(GraphQLQuery):
    _odoo_model = "link.tracker"
