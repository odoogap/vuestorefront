# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint
import werkzeug

from werkzeug import urls

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_adyen import utils as adyen_utils
from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class AdyenControllerInherit(AdyenController):

    _webhook_url = AdyenController()._webhook_url

    @http.route('/payment/adyen/payments', type='json', auth='public')
    def adyen_payments(
            self, provider_id, reference, converted_amount, currency_id, partner_id, payment_method,
            access_token, browser_info=None
    ):
        """ Make a payment request and process the feedback data.

        :param int provider_id: The provider handling the transaction, as a `payment.provider` id
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
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id).exists()
        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])

        shopper_ip = payment_utils.get_customer_ip_address()
        if tx_sudo.created_on_vsf:
            if request.httprequest.headers.environ.get('HTTP_REAL_IP', False) and \
                    request.httprequest.headers.environ['HTTP_REAL_IP']:
                shopper_ip = request.httprequest.headers.environ['HTTP_REAL_IP']

        data = {
            'merchantAccount': provider_sudo.adyen_merchant_account,
            'amount': {
                'value': converted_amount,
                'currency': request.env['res.currency'].browse(currency_id).name,  # ISO 4217
            },
            'reference': reference,
            'paymentMethod': payment_method,
            'shopperReference': provider_sudo._adyen_compute_shopper_reference(partner_id),
            'recurringProcessingModel': 'CardOnFile',  # Most susceptible to trigger a 3DS check
            'shopperIP': shopper_ip,
            'shopperInteraction': 'Ecommerce',
            'shopperEmail': tx_sudo.partner_email,
            'shopperName': adyen_utils.format_partner_name(tx_sudo.partner_name),
            'telephoneNumber': tx_sudo.partner_phone,
            'storePaymentMethod': tx_sudo.tokenize,  # True by default on Adyen side
            # 'additionalData': {
            #     'allow3DS2': True
            # },
            'channel': 'web',  # Required to support 3DS
            'origin': provider_sudo.get_base_url(),  # Required to support 3DS
            'browserInfo': browser_info,  # Required to support 3DS
            'returnUrl': urls.url_join(
                provider_sudo.get_base_url(),
                # Include the reference in the return url to be able to match it after redirection.
                # The key 'merchantReference' is chosen on purpose to be the same as that returned
                # by the /payments endpoint of Adyen.
                f'/payment/adyen/return?merchantReference={reference}'
            ),
            **adyen_utils.include_partner_addresses(tx_sudo),
        }

        # Force the capture delay on Adyen side if the provider is not configured for capturing
        # payments manually. This is necessary because it's not possible to distinguish
        # 'AUTHORISATION' events sent by Adyen with the merchant account's capture delay set to
        # 'manual' from events with the capture delay set to 'immediate' or a number of hours. If
        # the merchant account is configured to capture payments with a delay but the provider is
        # not, we force the immediate capture to avoid considering authorized transactions as
        # captured on Odoo.
        if not provider_sudo.capture_manually:
            data.update(captureDelayHours=0)

        # Make the payment request to Adyen
        response_content = provider_sudo._adyen_make_request(
            url_field_name='adyen_checkout_api_url',
            endpoint='/payments',
            payload=data,
            method='POST'
        )

        # Handle the payment request response
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            reference, pprint.pformat(response_content)
        )
        tx_sudo._handle_notification_data(
            'adyen', dict(response_content, merchantReference=reference),  # Match the transaction
        )
        return response_content

    @http.route('/payment/adyen/return', type='http', auth='public', csrf=False, save_session=False)
    def adyen_return_from_3ds_auth(self, **data):
        """ Process the authentication data sent by Adyen after redirection from the 3DS1 page.

        The route is flagged with `save_session=False` to prevent Odoo from assigning a new session
        to the user if they are redirected to this route with a POST request. Indeed, as the session
        cookie is created without a `SameSite` attribute, some browsers that don't implement the
        recommended default `SameSite=Lax` behavior will not include the cookie in the redirection
        request from the payment provider to Odoo. As the redirection to the '/payment/status' page
        will satisfy any specification of the `SameSite` attribute, the session of the user will be
        retrieved and with it the transaction which will be immediately post-processed.

        :param dict data: The authentication result data. May include custom params sent to Adyen in
                          the request to allow matching the transaction when redirected here.
        """
        payment_transaction = data.get('merchantReference') and request.env['payment.transaction'].sudo().search(
            [('reference', 'in', [data.get('merchantReference')])], limit=1
        )

        # Check the Order and respective website related with the transaction
        # Check the payment_return url for the success and error pages
        # Pass the transaction_id on the session
        sale_order_ids = payment_transaction.sale_order_ids.ids
        sale_order = request.env['sale.order'].sudo().search([
            ('id', 'in', sale_order_ids), ('website_id', '!=', False)
        ], limit=1)

        # Get Website
        website = sale_order.website_id
        # Redirect to VSF
        vsf_payment_success_return_url = website.vsf_payment_success_return_url
        vsf_payment_error_return_url = website.vsf_payment_error_return_url

        request.session["__payment_monitored_tx_ids__"] = [payment_transaction.id]

        # Retrieve the transaction based on the reference included in the return url
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'adyen', data
        )

        # Overwrite the operation to force the flow to 'redirect'. This is necessary because even
        # thought Adyen is implemented as a direct payment provider, it will redirect the user out
        # of Odoo in some cases. For instance, when a 3DS1 authentication is required, or for
        # special payment methods that are not handled by the drop-in (e.g. Sofort).
        tx_sudo.operation = 'online_redirect'

        # Query and process the result of the additional actions that have been performed
        _logger.info(
            "handling redirection from Adyen for transaction with reference %s with data:\n%s",
            tx_sudo.reference, pprint.pformat(data)
        )
        result = self.adyen_payment_details(
            tx_sudo.provider_id.id,
            data['merchantReference'],
            {
                'details': {
                    'redirectResult': data['redirectResult'],
                },
            },
        )

        if payment_transaction.created_on_vsf:
            # For Redirect 3DS2 and MobilePay (Success flow)
            if result and result.get('resultCode') and result['resultCode'] == 'Authorised':

                # Confirm sale order
                PaymentPostProcessing().poll_status()

                return werkzeug.utils.redirect(vsf_payment_success_return_url)

            # For Redirect 3DS2 and MobilePay (Cancel/Error flow)
            elif result and result.get('resultCode') and result['resultCode'] in ['Refused', 'Cancelled']:

                return werkzeug.utils.redirect(vsf_payment_error_return_url)

        else:
            # Redirect the user to the status page
            return request.redirect('/payment/status')

    @http.route(_webhook_url, type='json', auth='public')
    def adyen_webhook(self):
        """ Process the data sent by Adyen to the webhook based on the event code.

        See https://docs.adyen.com/development-resources/webhooks/understand-notifications for the
        exhaustive list of event codes.

        :return: The '[accepted]' string to acknowledge the notification
        :rtype: str
        """
        data = request.dispatcher.jsonrequest
        for notification_item in data['notificationItems']:
            notification_data = notification_item['NotificationRequestItem']

            _logger.info(
                "notification received from Adyen with data:\n%s", pprint.pformat(notification_data)
            )
            PaymentTransaction = request.env['payment.transaction']
            try:
                payment_transaction = notification_data.get('merchantReference') and PaymentTransaction.sudo().search(
                    [('reference', 'in', [notification_data.get('merchantReference')])], limit=1
                )

                # Check the integrity of the notification
                tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                    'adyen', notification_data
                )
                self._verify_notification_signature(notification_data, tx_sudo)

                # Check whether the event of the notification succeeded and reshape the notification
                # data for parsing
                success = notification_data['success'] == 'true'
                event_code = notification_data['eventCode']
                if event_code == 'AUTHORISATION' and success:
                    notification_data['resultCode'] = 'Authorised'
                elif event_code == 'CANCELLATION':
                    notification_data['resultCode'] = 'Cancelled' if success else 'Error'
                elif event_code in ['REFUND', 'CAPTURE']:
                    notification_data['resultCode'] = 'Authorised' if success else 'Error'
                else:
                    continue  # Don't handle unsupported event codes and failed events

                # Handle the notification data as if they were feedback of a S2S payment request
                tx_sudo._handle_notification_data('adyen', notification_data)

                # Case the transaction was created on vsf (Success flow)
                if event_code == 'AUTHORISATION' and success and payment_transaction.created_on_vsf:
                    # Check the Order and respective website related with the transaction
                    # Check the payment_return url for the success and error pages
                    sale_order_ids = payment_transaction.sale_order_ids.ids
                    sale_order = request.env['sale.order'].sudo().search([
                        ('id', 'in', sale_order_ids), ('website_id', '!=', False)
                    ], limit=1)

                    # Get Website
                    website = sale_order.website_id
                    # Redirect to VSF
                    vsf_payment_success_return_url = website.vsf_payment_success_return_url

                    request.session["__payment_monitored_tx_ids__"] = [payment_transaction.id]

                    # Confirm sale order
                    PaymentPostProcessing().poll_status()

                    return werkzeug.utils.redirect(vsf_payment_success_return_url)

            except ValidationError:  # Acknowledge the notification to avoid getting spammed
                _logger.exception("unable to handle the notification data; skipping to acknowledge")

        return '[accepted]'  # Acknowledge the notification
