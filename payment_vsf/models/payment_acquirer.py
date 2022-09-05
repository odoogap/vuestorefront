# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    # Configuration fields
    redirect_form_view_id = fields.Many2one(
        string="Redirect Form Template", comodel_name='ir.ui.view',
        help="The template rendering a form submitted to redirect the user when making a payment",
        domain=[('type', '=', 'qweb')])
    inline_form_view_id = fields.Many2one(
        string="Inline Form Template", comodel_name='ir.ui.view',
        help="The template rendering the inline payment form when making a direct payment",
        domain=[('type', '=', 'qweb')])

    # Feature support fields

    # support_refund = fields.Selection(
    #     string="Type of Refund Supported",
    #     selection=[('full_only', "Full Only"), ('partial', "Partial")],
    # )

    # support_authorization = fields.Boolean(string="Authorize Mechanism Supported")
    authorize_implemented = fields.Boolean('Authorize Mechanism Supported', compute='_compute_feature_support')

    # support_fees_computation = fields.Boolean(string="Fees Computation Supported")
    fees_implemented = fields.Boolean('Fees Computation Supported', compute='_compute_feature_support')

    # support_tokenization = fields.Boolean(string="Tokenization Supported")
    token_implemented = fields.Boolean('Saving Card Data supported', compute='_compute_feature_support',
                                       search='_search_is_tokenized')

    # allow_tokenization = fields.Boolean(
    #     string="Allow Saving Payment Methods",
    #     help="This controls whether customers can save their payment methods as payment tokens.\n"
    #          "A payment token is an anonymous link to the payment method details saved in the\n"
    #          "acquirer's database, allowing the customer to reuse it for a next purchase.")

    save_token = fields.Selection([
        ('none', 'Never'),
        ('ask', 'Let the customer decide'),
        ('always', 'Always')],
        string='Save Cards', default='none',
        help="This option allows customers to save their credit card as a payment token and to reuse it for a later purchase. "
             "If you manage subscriptions (recurring invoicing), you need it to automatically charge the customer when you "
             "issue an invoice.")
