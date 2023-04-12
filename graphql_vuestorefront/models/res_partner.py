# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_reg_no = fields.Char('Company Registration Number')
