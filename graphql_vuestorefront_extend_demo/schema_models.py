# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.graphql_vuestorefront.schema import GraphQLType, GraphQLQuery


# dynamic types

class LinkTracker(GraphQLType):
    _odoo_model = "link.tracker"


class LinkTrackerQuery(GraphQLQuery):
    _odoo_model = "link.tracker"


class CalendarEvent(GraphQLType):
    _odoo_model = "calendar.event"


class CalendarEventQuery(GraphQLQuery):
    _odoo_model = "calendar.event"
