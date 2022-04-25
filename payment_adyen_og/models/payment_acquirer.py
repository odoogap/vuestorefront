# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.addons.payment_adyen_og.const import SUPPORTED_CURRENCIES


class AcquirerAdyen(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('adyen_og', 'Adyen OG')
    ], ondelete={'adyen_og': 'set default'})
    adyen_merchant_account = fields.Char('Merchant Account', required_if_provider='adyen_og', groups='base.group_user')
    adyen_skin_code = fields.Char('Skin Code', required_if_provider='adyen_og', groups='base.group_user')
    adyen_skin_hmac_key = fields.Char('Skin HMAC Key', required_if_provider='adyen_og', groups='base.group_user')

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist Adyen acquirers when the currency is not supported. """
        acquirers = super()._get_compatible_acquirers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and ((currency.name not in SUPPORTED_CURRENCIES) or (
                currency.name in SUPPORTED_CURRENCIES and not currency.active)):
            acquirers = acquirers.filtered(lambda a: a.provider != 'adyen_og')

        return acquirers

    @api.model
    def _get_adyen_urls(self, environment):
        """ Adyen URLs: yhpp: hosted payment page: pay.shtml for single, select.shtml for multiple """
        return {
            'adyen_form_url': 'https://%s.adyen.com/hpp/pay.shtml' % ('live' if environment == 'prod' else environment),
        }

    def _adyen_get_api_url(self):
        """ Return the API URL according to the acquirer state.

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_adyen_urls(environment)['adyen_form_url']

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'adyen_og':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_adyen_og.payment_method_adyen_og').id
