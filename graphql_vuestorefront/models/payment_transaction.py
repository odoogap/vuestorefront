# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, api, fields, tools, _


class PaymentTransactionInherit(models.Model):
    _inherit = 'payment.transaction'

    created_on_vsf = fields.Boolean(string='Created on Vsf?', default=False)

    def _set_pending(self, state_message=None):
        """
            Overwrite the following steps:

            1- Do not update the Transaction to "Pending", keep the transaction in "Draft";
            2- Do not update the SO to 'sent' State;
            3- Do not send the quotation email confirmation;
            4- Do not Log the message on the SO chatter;

            These steps will prevent the creation of a new Cart.
            If the customer stops the payment process, the Cart will remain active in the current session.
            To ensure this behavior, we need to keep the last transaction in "Draft".
        """
        for record in self:
            if not record.created_on_vsf:
                super(PaymentTransactionInherit, record)._set_pending(state_message=state_message)
            else:
                allowed_states = ('draft',)
                target_state = 'draft'
                # txs_to_process
                self._update_state(allowed_states, target_state, state_message=None)
