# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.http import request
import os


class AppleMerchantIDController(http.Controller):

    @http.route('/.well-known/apple-developer-merchantid-domain-association', type='http', auth='public')
    def apple_merchant_id(self, **kw):
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'static', 'description', 'apple-developer-merchantid-domain-association')
        )

        try:
            with open(file_path, 'r') as file:
                file_content = file.read()

            headers = [('Content-Type', 'text/plain')]
            return request.make_response(file_content, headers)

        # Return error 404 - Not Found
        except FileNotFoundError:
            return request.not_found()
