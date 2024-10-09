# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment_stripe.const import HANDLED_WEBHOOK_EVENTS
from odoo.addons.payment_stripe.controllers.main import StripeController
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class StripeControllerInherit(StripeController):
    _return_url = StripeController()._return_url
    _webhook_url = StripeController()._webhook_url
    _apple_pay_domain_association_url = StripeController()._apple_pay_domain_association_url
    WEBHOOK_AGE_TOLERANCE = StripeController().WEBHOOK_AGE_TOLERANCE

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def stripe_return(self, **data):
        """ Process the notification data sent by Stripe after redirection from payment.

        Customers go through this route regardless of whether the payment was direct or with
        redirection to Stripe or to an external service (e.g., for strong authentication).

        :param dict data: The notification data, including the reference appended to the URL in
                          `_get_specific_processing_values`.
        """
        # Retrieve the transaction based on the reference included in the return url.
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'stripe', data
        )

        # Check the Order and respective website related with the transaction
        # Check the payment_return url for the success and error pages
        # Pass the transaction_id on the session
        sale_order_ids = tx_sudo.sale_order_ids.ids
        sale_order = request.env['sale.order'].sudo().search([
            ('id', 'in', sale_order_ids), ('website_id', '!=', False)
        ], limit=1)

        # Get Website
        website = sale_order.website_id
        # Redirect to VSF
        vsf_payment_success_return_url = website.vsf_payment_success_return_url
        vsf_payment_error_return_url = website.vsf_payment_error_return_url

        request.session["__payment_monitored_tx_id__"] = tx_sudo.id

        payment_intent = {}
        if tx_sudo.operation != 'validation':
            # Fetch the PaymentIntent and PaymentMethod objects from Stripe.
            payment_intent = tx_sudo.provider_id._stripe_make_request(
                f'payment_intents/{data.get("payment_intent")}',
                payload={'expand[]': 'payment_method'},  # Expand all required objects.
                method='GET',
            )
            _logger.info("Received payment_intents response:\n%s", pprint.pformat(payment_intent))
            self._include_payment_intent_in_notification_data(payment_intent, data)
        else:
            # Fetch the SetupIntent and PaymentMethod objects from Stripe.
            setup_intent = tx_sudo.provider_id._stripe_make_request(
                f'setup_intents/{data.get("setup_intent")}',
                payload={'expand[]': 'payment_method'},  # Expand all required objects.
                method='GET',
            )
            _logger.info("Received setup_intents response:\n%s", pprint.pformat(setup_intent))
            self._include_setup_intent_in_notification_data(setup_intent, data)

        # Handle the notification data crafted with Stripe API's objects.
        tx_sudo._handle_notification_data('stripe', data)

        # Condition used for VSF
        if tx_sudo.created_on_vsf:
            if payment_intent:
                if payment_intent.get('status') and payment_intent['status'] == 'succeeded':
                    # Confirm sale order
                    PaymentPostProcessing().poll_status()
                    return werkzeug.utils.redirect(vsf_payment_success_return_url)
                else:
                    return werkzeug.utils.redirect(vsf_payment_error_return_url)
        # Default Condition
        else:
            # Redirect the user to the status page.
            return request.redirect('/payment/status')
