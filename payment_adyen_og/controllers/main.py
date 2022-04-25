# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AdyenOGController(http.Controller):
    _return_url = '/payment/adyen/return/'

    @http.route([
        '/payment/adyen/return',
    ], type='http', auth='public', csrf=False)
    def adyen_return(self, **post):
        _logger.info('Beginning Adyen form_feedback with post data %s', pprint.pformat(post))  # debug
        if post.get('authResult') not in ['CANCELLED']:
            request.env['payment.transaction'].sudo()._handle_feedback_data('adyen_og', post)
        return werkzeug.utils.redirect('/payment/status')

    @http.route([
        '/payment/adyen/notification',
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
