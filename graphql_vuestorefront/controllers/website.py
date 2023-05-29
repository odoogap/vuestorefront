# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import http, SUPERUSER_ID
from odoo.http import content_disposition, request, Response

_logger = logging.getLogger(__name__)


class VSFWebsiteController(http.Controller):

    @http.route(['/download/invoices/<int:order_id>/'], type='http', auth="none", cors="*", website=False)
    def download_order_invoices_pdf(self, order_id, access_token=False):
        """ Download the Invoices Pdf """
        order = request.env['sale.order'].sudo().search([('id', '=', order_id)])

        if order and order.id and order.access_token == access_token:
            report = request.env.ref('account.account_invoices')
            pdf = report.with_user(SUPERUSER_ID).sudo()._render_qweb_pdf(order.invoice_ids.ids)[0]
            filename = 'Invoices_Order_{}.pdf'.format(order.name)
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
                ('Content-Disposition', content_disposition(filename)),
                ('Access-Control-Expose-Headers', 'Content-Disposition')
            ]
            return request.make_response(pdf, headers=pdfhttpheaders)

        else:
            _logger.info('The Sale Order %s does not exist or you do not have the rights to access it.', str(order_id))
            return Response(
                str('The Sale Order {} does not exist or you do not have the rights to access it.'.format(
                    str(order_id))),
                status=500
            )
