# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_confirmation_template(self):
        website = self.env['website'].get_current_website()
        return website.order_confirmation_email_template_id
