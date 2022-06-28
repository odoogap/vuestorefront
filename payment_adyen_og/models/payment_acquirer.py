# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
import requests
from odoo import _
from odoo import fields, models, api
from odoo.addons.payment_adyen.const import API_ENDPOINT_VERSIONS
from odoo.addons.payment_adyen_og.const import SUPPORTED_CURRENCIES
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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

    def _adyen_make_request(
            self, url_field_name, endpoint, endpoint_param=None, payload=None, method='POST'
    ):
        """ Overwrite method to post payment fail error in channel"""

        def _build_url(_base_url, _version, _endpoint):
            _base = _base_url.rstrip('/')  # Remove potential trailing slash
            _endpoint = _endpoint.lstrip('/')  # Remove potential leading slash
            return f'{_base}/V{_version}/{_endpoint}'

        self.ensure_one()
        base_url = self[url_field_name]  # Restrict request URL to the stored API URL fields
        version = API_ENDPOINT_VERSIONS[endpoint]
        endpoint = endpoint if not endpoint_param else endpoint.format(endpoint_param)
        url = _build_url(base_url, version, endpoint)
        headers = {'X-API-Key': self.adyen_api_key}
        adyen_payment_channel = self.sudo().env.ref(
            'payment_adyen_og.channel_adyen_payment_announcement')
        partner = self.env.user.partner_id
        try:
            response = requests.request(method, url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            message = "Adyen: Could not establish the connection to the API, Reference %s." % payload.get('reference',
                                                                                                          '')
            adyen_payment_channel.message_post(body=message, subtype_xmlid='mail.mt_comment', partner_ids=partner.ids)
            _logger.exception("unable to reach endpoint at %s", url)
            self.env.cr.commit()
            raise ValidationError("Adyen: " + _("Could not establish the connection to the API."))
        except requests.exceptions.HTTPError as error:
            message = "Adyen: The communication with the API failed, Reference %s." % payload.get('reference', '')
            _logger.exception(
                "invalid API request at %s with data %s: %s", url, payload, error.response.text
            )
            adyen_payment_channel.message_post(body=message, subtype_xmlid='mail.mt_comment', partner_ids=partner.ids)
            self.env.cr.commit()
            raise ValidationError("Adyen: " + _("The communication with the API failed."))
        return response.json()
