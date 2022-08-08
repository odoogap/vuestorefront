# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    created_on_vsf = fields.Boolean(string='Created on Vsf?', default=False)
