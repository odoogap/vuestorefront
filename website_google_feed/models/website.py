# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class Website(models.Model):
    _inherit = 'website'

    google_feed_expire_time = fields.Integer(default=12)
