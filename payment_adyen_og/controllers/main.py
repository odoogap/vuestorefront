# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint
import werkzeug

from odoo import http
from werkzeug import urls
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_adyen.controllers.main import AdyenController

_logger = logging.getLogger(__name__)


class AdyenControllerInherit(AdyenController):

    @http.route('/payment/adyen/payments', type='json', auth='public')
    def adyen_payments(
            self, acquirer_id, reference, converted_amount, currency_id, partner_id, payment_method,
            access_token, browser_info=None
    ):
        """ Make a payment request and process the feedback data.

        :param int acquirer_id: The acquirer handling the transaction, as a `payment.acquirer` id
        :param str reference: The reference of the transaction
        :param int converted_amount: The amount of the transaction in minor units of the currency
        :param int currency_id: The currency of the transaction, as a `res.currency` id
        :param int partner_id: The partner making the transaction, as a `res.partner` id
        :param dict payment_method: The details of the payment method used for the transaction
        :param str access_token: The access token used to verify the provided values
        :param dict browser_info: The browser info to pass to Adyen
        :return: The JSON-formatted content of the response
        :rtype: dict
        """
        # Check that the transaction details have not been altered. This allows preventing users
        # from validating transactions by paying less than agreed upon.
        if not payment_utils.check_access_token(
                access_token, reference, converted_amount, partner_id
        ):
            raise ValidationError("Adyen: " + _("Received tampered payment request data."))

        # Make the payment request to Adyen
        acquirer_sudo = request.env['payment.acquirer'].sudo().browse(acquirer_id).exists()

        if acquirer_sudo.provider == 'adyen_og':
            returnUrl = urls.url_join(
                acquirer_sudo.get_base_url(),
                # Include the reference in the return url to be able to match it after redirection.
                # The key 'merchantReference' is chosen on purpose to be the same as that returned
                # by the /payments endpoint of Adyen.
                f'/payment/adyen_og/return?merchantReference={reference}'
            )
        elif acquirer_sudo.provider == 'adyen':
            returnUrl = urls.url_join(
                acquirer_sudo.get_base_url(),
                # Include the reference in the return url to be able to match it after redirection.
                # The key 'merchantReference' is chosen on purpose to be the same as that returned
                # by the /payments endpoint of Adyen.
                f'/payment/adyen/return?merchantReference={reference}'
            )

        print('\n\n\n\n')
        print('RETURN URL')
        print(returnUrl)

        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        data = {
            'merchantAccount': acquirer_sudo.adyen_merchant_account,
            'amount': {
                'value': converted_amount,
                'currency': request.env['res.currency'].browse(currency_id).name,  # ISO 4217
            },
            'reference': reference,
            'paymentMethod': payment_method,
            'shopperReference': acquirer_sudo._adyen_compute_shopper_reference(partner_id),
            'recurringProcessingModel': 'CardOnFile',  # Most susceptible to trigger a 3DS check
            'shopperIP': payment_utils.get_customer_ip_address(),
            'shopperInteraction': 'Ecommerce',
            'storePaymentMethod': tx_sudo.tokenize,  # True by default on Adyen side
            'additionalData': {
                'allow3DS2': True
            },
            'channel': 'web',  # Required to support 3DS
            'origin': acquirer_sudo.get_base_url(),  # Required to support 3DS
            'browserInfo': browser_info,  # Required to support 3DS
            'returnUrl': returnUrl,
        }
        response_content = acquirer_sudo._adyen_make_request(
            url_field_name='adyen_checkout_api_url',
            endpoint='/payments',
            payload=data,
            method='POST'
        )

        # Handle the payment request response
        _logger.info("payment request response:\n%s", pprint.pformat(response_content))
        request.env['payment.transaction'].sudo()._handle_feedback_data(
            'adyen', dict(response_content, merchantReference=reference),  # Match the transaction
        )
        return response_content


class AdyenOGController(http.Controller):
    _return_url = '/payment/adyen_og/return/'

    @http.route([
        '/payment/adyen_og/return',
    ], type='http', auth='public', csrf=False)
    def adyen_return(self, **post):
        _logger.info('Beginning Adyen form_feedback with post data %s', pprint.pformat(post))  # debug
        if post.get('authResult') not in ['CANCELLED']:
            request.env['payment.transaction'].sudo()._handle_feedback_data('adyen_og', post)
        return werkzeug.utils.redirect('/payment/status')

    @http.route([
        '/payment/adyen_og/notification',
    ], type='http', auth='public', methods=['POST'], csrf=False)
    def adyen_notification(self, **post):
        tx = post.get('merchantReference') and request.env['payment.transaction'].sudo().search([('reference', 'in', [post.get('merchantReference')])], limit=1)
        if post.get('eventCode') in ['AUTHORISATION'] and tx:
            states = (post.get('merchantReference'), post.get('success'), tx.state)
            if (post.get('success') == 'true' and tx.state == 'done') or (post.get('success') == 'false' and tx.state in ['cancel', 'error']):
                _logger.info('Notification from Adyen for the reference %s: received %s, state is %s', states)
            else:
                _logger.warning('Notification from Adyen for the reference %s: received %s but state is %s', states)
        return '[accepted]'
