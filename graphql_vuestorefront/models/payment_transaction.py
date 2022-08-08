# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, api, fields, tools, _


class PaymentTransactionInherit(models.Model):
    _inherit = 'payment.transaction'

    def _set_pending(self, state_message=None):
        """
            Override of payment to not update the order to 'sent' State and to not sent the quotation email confirmation
        """

        for record in self:
            if not record.created_on_vsf:
                super(PaymentTransactionInherit, record)._set_pending(state_message=state_message)
            else:
                allowed_states = ('draft',)
                target_state = 'pending'
                txs_to_process = self._update_state(allowed_states, target_state, state_message)
                txs_to_process._log_received_message()
