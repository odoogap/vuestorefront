# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Website(models.Model):
    _inherit = 'website'

    google_feed_expire_time = fields.Integer(default=12)
