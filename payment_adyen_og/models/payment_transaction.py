# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
import pprint
import hmac
import hashlib
import binascii

from odoo import models, api, tools, _
from itertools import chain
from collections import OrderedDict
from werkzeug import urls
from odoo.exceptions import ValidationError
from odoo.tools.pycompat import to_text
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_adyen.const import API_ENDPOINT_VERSIONS
from odoo.addons.payment_adyen_og.const import SUPPORTED_CURRENCIES
from odoo.addons.payment_adyen_og.controllers.main import AdyenOGController

_logger = logging.getLogger(__name__)
API_ENDPOINT_VERSIONS['/payments/{}/captures'] = 67
API_ENDPOINT_VERSIONS['/payments/{}/cancels'] = 67


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _adyen_convert_amount(self, amount, currency):
        """
        Adyen requires the amount to be multiplied by 10^k,
        where k depends on the currency code.
        """
        k = SUPPORTED_CURRENCIES.get(currency.name, 2)
        paymentAmount = int(tools.float_round(amount, k) * (10 ** k))
        return paymentAmount

    def _adyen_generate_merchant_sig_sha256(self, inout, values):
        """ Generate the shasign for incoming or outgoing communications., when using the SHA-256
        signature.

        :param string inout: 'in' (odoo contacting adyen) or 'out' (adyen
                             contacting odoo). In this last case only some
                             fields should be contained (see e-Commerce basic)
        :param dict values: transaction values
        :return string: shasign
        """

        def escapeVal(val):
            if isinstance(val, int):
                return val
            if val is None:
                return ""
            return val.replace('\\', '\\\\').replace(':', '\\:')

        def signParams(parms):
            signing_string = ':'.join(escapeVal(v) for v in chain(parms.keys(), parms.values()))
            hm = hmac.new(hmac_key, signing_string.encode('utf-8'), hashlib.sha256)
            return base64.b64encode(hm.digest())

        assert inout in ('in', 'out')
        assert self.provider == 'adyen_og'

        if inout == 'in':
            # All the fields sent to Adyen must be included in the signature. ALL the fucking
            # fields, despite what is claimed in the documentation. For example, in
            # https://docs.adyen.com/developers/hpp-manual, it is stated: "The resURL parameter does
            # not need to be included in the signature." It's a trap, it must be included as well!
            keys = [
                'merchantReference', 'paymentAmount', 'currencyCode', 'shipBeforeDate', 'skinCode',
                'merchantAccount', 'sessionValidity', 'merchantReturnData', 'shopperEmail',
                'shopperReference', 'allowedMethods', 'blockedMethods', 'offset',
                'shopperStatement', 'recurringContract', 'billingAddressType',
                'deliveryAddressType', 'brandCode', 'countryCode', 'shopperLocale', 'orderData',
                'offerEmail', 'resURL',
            ]
        else:
            keys = [
                'authResult', 'merchantReference', 'merchantReturnData', 'paymentMethod',
                'pspReference', 'shopperLocale', 'skinCode',
            ]

        hmac_key = binascii.a2b_hex(self.acquirer_id.adyen_skin_hmac_key.encode('ascii'))
        raw_values = {k: values.get(k, '') for k in keys if k in values}
        raw_values_ordered = OrderedDict(sorted(raw_values.items(), key=lambda t: t[0]))

        return signParams(raw_values_ordered).decode('ascii')

    def _adyen_generate_merchant_sig(self, inout, values):
        """ Generate the shasign for incoming or outgoing communications, when using the SHA-1
        signature (deprecated by Adyen).

        :param string inout: 'in' (odoo contacting adyen) or 'out' (adyen
                             contacting odoo). In this last case only some
                             fields should be contained (see e-Commerce basic)
        :param dict values: transaction values

        :return string: shasign
        """
        assert inout in ('in', 'out')
        assert self.provider == 'adyen_og'

        if inout == 'in':
            keys = "paymentAmount currencyCode shipBeforeDate merchantReference skinCode merchantAccount sessionValidity shopperEmail shopperReference recurringContract allowedMethods blockedMethods shopperStatement merchantReturnData billingAddressType deliveryAddressType offset".split()
        else:
            keys = "authResult pspReference merchantReference skinCode merchantReturnData".split()

        def get_value(key):
            if values.get(key):
                return values[key]
            return ''

        sign = ''.join('%s' % get_value(k) for k in keys).encode('ascii')
        key = self.acquirer_id.adyen_skin_hmac_key.encode('ascii')
        return base64.b64encode(hmac.new(key, sign, hashlib.sha1).digest())

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Adyen-specific rendering values.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'adyen_og':
            return res

        base_url = self.acquirer_id.get_base_url()
        import datetime
        from dateutil import relativedelta

        paymentAmount = self._adyen_convert_amount(processing_values['amount'], self.currency_id)
        processing_values.update({
            'partner': self.partner_id,
            'partner_id': self.partner_id and self.partner_id.id,
            'partner_name': self.partner_name,
            'partner_lang': self.partner_lang,
            'partner_email': self.partner_email,
            'partner_zip': self.partner_zip,
            'partner_city': self.partner_city,
            'partner_address': self.partner_address,
            'partner_country_id': (self.partner_country_id and self.partner_country_id.id) or self.env.company.country_id.id,
            'partner_country': self.partner_country_id,
            'partner_phone': self.partner_phone,
            'partner_state': self.partner_state_id,
            'billing_partner': self.partner_id,
            'billing_partner_id': self.partner_id and self.partner_id.id,
            'billing_partner_name': self.partner_name,
            'billing_partner_lang': self.partner_lang,
            'billing_partner_email': self.partner_email,
            'billing_partner_zip': self.partner_zip,
            'billing_partner_city': self.partner_city,
            'billing_partner_address': self.partner_address,
            'billing_partner_country_id': (self.partner_country_id and self.partner_country_id.id) or self.env.company.country_id.id,
            'billing_partner_country': self.partner_country_id,
            'billing_partner_phone': self.partner_phone,
            'billing_partner_state': self.partner_state_id,
            'api_url': self.acquirer_id._adyen_get_api_url(),
        })
        processing_values.setdefault('return_url', '/payment/status')
        if self.provider == 'adyen_og' and len(self.acquirer_id.adyen_skin_hmac_key) == 64:
            tmp_date = datetime.datetime.today() + relativedelta.relativedelta(days=1)

            processing_values.update({
                'merchantReference': processing_values['reference'],
                'paymentAmount': '%d' % paymentAmount,
                'currencyCode': self.currency_id and self.currency_id.name or '',
                'shipBeforeDate': tmp_date.strftime('%Y-%m-%d'),
                'skinCode': self.acquirer_id.adyen_skin_code,
                'merchantAccount': self.acquirer_id.adyen_merchant_account,
                'shopperLocale': processing_values.get('partner_lang', ''),
                'sessionValidity': tmp_date.isoformat('T')[:19] + "Z",
                'resURL': urls.url_join(base_url, AdyenOGController._return_url),
                'merchantReturnData': '{"return_url": "/payment/status"}',
                'shopperEmail': processing_values.get('partner_email') or processing_values.get(
                    'billing_partner_email') or '',
            })
            processing_values['merchantSig'] = self._adyen_generate_merchant_sig_sha256('in', processing_values)

        else:
            tmp_date = datetime.date.today() + relativedelta.relativedelta(days=1)

            processing_values.update({
                'merchantReference': processing_values['reference'],
                'paymentAmount': '%d' % paymentAmount,
                'currencyCode': self.currency_id and self.currency_id.name or '',
                'shipBeforeDate': tmp_date,
                'skinCode': self.acquirer_id.adyen_skin_code,
                'merchantAccount': self.acquirer_id.adyen_merchant_account,
                'shopperLocale': processing_values.get('partner_lang'),
                'sessionValidity': tmp_date,
                'resURL': urls.url_join(base_url, AdyenOGController._return_url),
                'merchantReturnData': '{"return_url": "/payment/status"}',
            })
            processing_values['merchantSig'] = self._adyen_generate_merchant_sig('in', processing_values)

        return processing_values

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on Adyen data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)

        if provider != 'adyen_og':
            return tx

        reference, pspReference = data.get('merchantReference'), data.get('pspReference')
        if not reference or not pspReference:
            error_msg = _('Adyen: received data with missing reference (%s) or missing pspReference (%s)') % (
            reference, pspReference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use pspReference ?
        tx = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('Adyen: received data for reference %s') % reference
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        if len(tx.acquirer_id.adyen_skin_hmac_key) == 64:
            shasign_check = tx._adyen_generate_merchant_sig_sha256('out', data)
        else:
            shasign_check = tx._adyen_generate_merchant_sig('out', data)
        if to_text(shasign_check) != to_text(data.get('merchantSig')):
            # When is one capture Manually we need to update the merchantSig
            if data.get('status') == 'received':
                data['merchantSig'] = shasign_check
            else:
                error_msg = _('Adyen: invalid merchantSig, received %s, computed %s') % (
                data.get('merchantSig'), shasign_check)
                _logger.warning(error_msg)
                raise ValidationError(error_msg)

        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Adyen data.

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        if self.provider != 'adyen_og':
            return super()._process_feedback_data(data)

        payment_state = data.get('resultCode')
        status = data.get('authResult', 'PENDING')
        if status == 'AUTHORISED':
            self.write({'acquirer_reference': data.get('pspReference')})
            # Capture Manually
            if self.acquirer_id.capture_manually:
                self._set_authorized()
            else:
                self._set_done()
            return True
        elif status == 'PENDING':
            self.write({'acquirer_reference': data.get('pspReference')})
            # Capture Manually
            if payment_state and payment_state == 'received' and data.get('paymentPspReference'):
                self._set_done()
            else:
                self._set_pending()
            return True
        else:
            error = _('Adyen: feedback error')
            _logger.info(error)
            self._set_canceled(state_message=error)
            return False

    def _send_capture_request(self):
        """ Override of payment to send a capture request to Adyen."""
        super()._send_capture_request()
        if self.provider != 'adyen_og':
            return

        amount = sum(self.sale_order_ids.mapped('amount_total'))
        if self.amount > amount:
            self.amount = amount

        # Make the capture request to Adyen
        converted_amount = payment_utils.to_minor_currency_units(
            self.amount,
            self.currency_id,
            arbitrary_decimal_number=SUPPORTED_CURRENCIES.get(self.currency_id.name, 2)
        )
        data = {
            'merchantAccount': self.acquirer_id.adyen_merchant_account,
            'amount': {
                'value': converted_amount,
                'currency': self.currency_id.name,
            },
            'reference': self.reference,
        }
        response_content = self.acquirer_id._adyen_make_request(
            url_field_name='adyen_checkout_api_url',
            endpoint='/payments/{}/captures',
            endpoint_param=self.acquirer_reference,
            payload=data,
            method='POST'
        )
        _logger.info("capture request response:\n%s", pprint.pformat(response_content))
        feedback_data = response_content
        feedback_data.update({
            'resultCode': response_content.get('status', ''),
            'merchantReference': response_content.get('reference', '')
        })
        self._handle_feedback_data('adyen_og', feedback_data)
        return True

    def _send_void_request(self):
        """ Override of payment to cancel payment request to Adyen."""
        super()._send_void_request()
        if self.provider != 'adyen_og':
            return

        data = {
            'merchantAccount': self.acquirer_id.adyen_merchant_account,
            'reference': self.reference,
        }
        response_content = self.acquirer_id._adyen_make_request(
            url_field_name='adyen_checkout_api_url',
            endpoint='/payments/{}/cancels',
            endpoint_param=self.acquirer_reference,
            payload=data,
            method='POST'
        )
        _logger.info("capture request response:\n%s", pprint.pformat(response_content))
        feedback_data = response_content
        feedback_data.update({
            'resultCode': response_content.get('status', ''),
            'merchantReference': response_content.get('reference', ''),
            'authResult': 'CANCELED'
        })
        self._handle_feedback_data('adyen_og', feedback_data)
        return True