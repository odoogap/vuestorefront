# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class SaleOrderLine(models.AbstractModel):
    _inherit = 'sale.order.line'


    def _show_in_cart(self):
        # Hide downpayment and reward lines from website_order_line
        return not self.is_downpayment and not self.is_reward_line and super()._show_in_cart()