# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    provider = fields.Selection(related='acquirer_id.provider')

    # transaction_ids = fields.One2many(string="Payment Transactions", comodel_name='payment.transaction', inverse_name='token_id')
    payment_ids = fields.One2many('payment.transaction', 'payment_token_id', 'Payment Transactions')

    #=== CRUD METHODS ===#

    def write(self, values):
        """ Delegate the handling of active state switch to dedicated methods.

        Unless an exception is raised in the handling methods, the toggling proceeds no matter what.
        This is because allowing users to hide their saved payment methods comes before making sure
        that the recorded payment details effectively get deleted.

        :return: The result of the write
        :rtype: bool
        """
        # Let acquirers handle activation/deactivation requests
        if 'active' in values:
            for token in self:
                # Call handlers in sudo mode because this method might have been called by RPC
                if values['active'] and not token.active:
                    token.sudo()._handle_reactivation_request()
                elif not values['active'] and token.active:
                    token.sudo()._handle_deactivation_request()

        # Proceed with the toggling of the active state
        return super().write(values)

    #=== BUSINESS METHODS ===#

    def _handle_deactivation_request(self):
        """ Handle the request for deactivation of the token.

        For an acquirer to support deactivation of tokens, or perform additional operations when a
        token is deactivated, it must overwrite this method and raise an UserError if the token
        cannot be deactivated.

        Note: self.ensure_one()

        :return: None
        """
        self.ensure_one()

    def _handle_reactivation_request(self):
        """ Handle the request for reactivation of the token.

        For an acquirer to support reactivation of tokens, or perform additional operations when a
        token is reactivated, it must overwrite this method and raise an UserError if the token
        cannot be reactivated.

        Note: self.ensure_one()

        :return: None
        """
        self.ensure_one()
