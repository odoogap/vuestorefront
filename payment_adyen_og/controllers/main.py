# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging
import pprint
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment_adyen.controllers.main import AdyenController
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class AdyenControllerInherit(AdyenController):

    @http.route('/payment/adyen/return', type='http', auth='public', csrf=False, save_session=False)
    def adyen_return_from_redirect(self, **data):
        """ Process the data returned by Adyen after redirection.

        The route is flagged with `save_session=False` to prevent Odoo from assigning a new session
        to the user if they are redirected to this route with a POST request. Indeed, as the session
        cookie is created without a `SameSite` attribute, some browsers that don't implement the
        recommended default `SameSite=Lax` behavior will not include the cookie in the redirection
        request from the payment provider to Odoo. As the redirection to the '/payment/status' page
        will satisfy any specification of the `SameSite` attribute, the session of the user will be
        retrieved and with it the transaction which will be immediately post-processed.

        :param dict data: Feedback data. May include custom params sent to Adyen in the request to
                          allow matching the transaction when redirected here.
        """
        payment_transaction = data.get('merchantReference') and request.env['payment.transaction'].sudo().search(
            [('reference', 'in', [data.get('merchantReference')])], limit=1
        )

        acquirer = payment_transaction.acquirer_id

        if acquirer.provider == 'adyen':
            # Retrieve the transaction based on the reference included in the return url
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data(
                'adyen', data
            )

            # Overwrite the operation to force the flow to 'redirect'. This is necessary because even
            # thought Adyen is implemented as a direct payment provider, it will redirect the user out
            # of Odoo in some cases. For instance, when a 3DS1 authentication is required, or for
            # special payment methods that are not handled by the drop-in (e.g. Sofort).
            tx_sudo.operation = 'online_redirect'

            # Query and process the result of the additional actions that have been performed
            _logger.info("handling redirection from Adyen with data:\n%s", pprint.pformat(data))
            self.adyen_payment_details(
                tx_sudo.acquirer_id.id,
                data['merchantReference'],
                {
                    'details': {
                        'redirectResult': data['redirectResult'],
                    },
                },
            )

        elif acquirer.provider == 'adyen_og':
            # Get the route payment/adyen/return of the v14
            _logger.info('Beginning Adyen form_feedback with post data %s', pprint.pformat(data))  # debug
            if data.get('authResult') not in ['CANCELLED']:
                request.env['payment.transaction'].sudo()._handle_feedback_data('adyen_og', data)

        sale_order_ids = payment_transaction.sale_order_ids.ids
        sale_order = request.env['sale.order'].sudo().search([
            ('id', 'in', sale_order_ids), ('website_id', '!=', False)
        ], limit=1)

        # Get Website
        website = sale_order.website_id
        # Redirect to VSF
        vsf_payment_return_url = website.vsf_payment_return_url

        request.session["__payment_monitored_tx_ids__"] = [payment_transaction.id]

        # Confirm sale order
        PaymentPostProcessing().poll_status()

        # Clear the payment_monitored_tx_ids
        request.session['__payment_monitored_tx_ids__'] = []

        return werkzeug.utils.redirect(vsf_payment_return_url)

    @http.route('/payment/adyen/notification', type='json', auth='public')
    def adyen_notification(self):
        """ Process the data sent by Adyen to the webhook based on the event code.

        See https://docs.adyen.com/development-resources/webhooks/understand-notifications for the
        exhaustive list of event codes.

        :return: The '[accepted]' string to acknowledge the notification
        :rtype: str
        """
        data = json.loads(request.httprequest.data)
        for notification_item in data['notificationItems']:
            notification_data = notification_item['NotificationRequestItem']

            # Check the source and integrity of the notification
            received_signature = notification_data.get('additionalData', {}).get('hmacSignature')
            PaymentTransaction = request.env['payment.transaction']
            try:

                payment_transaction = notification_data.get('merchantReference') and PaymentTransaction.sudo().search(
                    [('reference', 'in', [notification_data.get('merchantReference')])], limit=1
                )

                acquirer = payment_transaction.acquirer_id

                if acquirer.provider == 'adyen':
                    acquirer_sudo = PaymentTransaction.sudo()._get_tx_from_feedback_data(
                        'adyen', notification_data
                    ).acquirer_id  # Find the acquirer based on the transaction
                    if not self._verify_notification_signature(
                            received_signature, notification_data, acquirer_sudo.adyen_hmac_key
                    ):
                        continue

                    # Check whether the event of the notification succeeded and reshape the notification
                    # data for parsing
                    _logger.info("notification received:\n%s", pprint.pformat(notification_data))
                    success = notification_data['success'] == 'true'
                    event_code = notification_data['eventCode']
                    if event_code == 'AUTHORISATION' and success:
                        notification_data['resultCode'] = 'Authorised'

                        # # Case the transaction was created on vsf
                        # if payment_transaction.created_on_vsf:
                        #     sale_order_ids = payment_transaction.sale_order_ids.ids
                        #     sale_order = request.env['sale.order'].sudo().search([
                        #         ('id', 'in', sale_order_ids), ('website_id', '!=', False)
                        #     ], limit=1)
                        #
                        #     # Get Website
                        #     website = sale_order.website_id
                        #     # Redirect to VSF
                        #     vsf_payment_return_url = website.vsf_payment_return_url
                        #
                        #     request.session["__payment_monitored_tx_ids__"] = [payment_transaction.id]
                        #
                        #     # Confirm sale order
                        #     PaymentPostProcessing().poll_status()
                        #
                        #     # Clear the payment_monitored_tx_ids
                        #     request.session['__payment_monitored_tx_ids__'] = []
                        #
                        #     return werkzeug.utils.redirect(vsf_payment_return_url)

                    elif event_code == 'CANCELLATION' and success:
                        notification_data['resultCode'] = 'Cancelled'
                    elif event_code == 'REFUND':
                        notification_data['resultCode'] = 'Authorised' if success else 'Error'
                    else:
                        continue  # Don't handle unsupported event codes and failed events

                    # Handle the notification data as a regular feedback
                    PaymentTransaction.sudo()._handle_feedback_data('adyen', notification_data)

                # Get the route payment/adyen/notification of the v14
                elif acquirer.provider == 'adyen_og':
                    tx = notification_data.get('merchantReference') and PaymentTransaction.sudo().search(
                        [('reference', 'in', [notification_data.get('merchantReference')])], limit=1)
                    if notification_data.get('eventCode') in ['AUTHORISATION'] and tx:
                        states = (
                            notification_data.get('merchantReference'),
                            notification_data.get('success'),
                            tx.state
                        )
                        if (notification_data.get('success') == 'true' and tx.state == 'done') or (
                                notification_data.get('success') == 'false' and tx.state in ['cancel', 'error']
                        ):
                            _logger.info(
                                'Notification from Adyen for the reference %s: received %s, state is %s',
                                states[0], states[1], states[2]
                            )
                        else:
                            _logger.warning(
                                'Notification from Adyen for the reference %s: received %s but state is %s',
                                states[0], states[1], states[2]
                            )

            except ValidationError:  # Acknowledge the notification to avoid getting spammed
                _logger.exception("unable to handle the notification data; skipping to acknowledge")

        return '[accepted]'  # Acknowledge the notification


class AdyenOGController(http.Controller):
    _return_url = '/payment/adyen/return/'
