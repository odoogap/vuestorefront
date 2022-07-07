# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, tools


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    display_as = fields.Char(string="Displayed as", help="Description of the acquirer for customers",
        translate=True)
