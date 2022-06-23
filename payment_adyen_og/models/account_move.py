# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_paid(self):
        res = super(AccountMove, self).action_invoice_paid()
        if self.move_type == 'out_refund' and self.state == 'posted' and self.payment_state == 'paid':
            for transaction in self.reversed_entry_id.transaction_ids:
                if transaction.acquirer_id and transaction.acquirer_id.provider == 'adyen_og':
                    transaction.with_context(refund_invoice_id=self.id).action_refund(amount_to_refund=self.amount_total)
        return res
