# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, api, fields, tools, _


class PaymentTransactionInherit(models.Model):
    _inherit = 'payment.transaction'

    created_on_vsf = fields.Boolean(string='Created on Vsf?', default=False)

    def _set_pending(self, state_message=None):
        """
            Overwrite steps:

            1- Not update the Transaction to "Pending" ;
            2- Not update the SO to 'sent' State;
            3- Not send the quotation email confirmation;
            4- Not Log the message on the SO chatter;
        """
        for record in self:
            if not record.created_on_vsf:
                super(PaymentTransactionInherit, record)._set_pending(state_message=state_message)
            else:
                allowed_states = ('draft',)
                target_state = 'draft'
                # txs_to_process
                self._update_state(allowed_states, target_state, state_message=None)
