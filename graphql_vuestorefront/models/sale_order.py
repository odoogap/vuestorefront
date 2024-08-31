# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_preview_sale_order(self):
        action = super().action_preview_sale_order()
        action['url'] = self.get_portal_url()
        return action
