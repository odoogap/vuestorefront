# -*- coding: utf-8 -*-
# Copyright 2021 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from odoo import models, fields, api


class Website(models.Model):
    _inherit = 'website'

    vsf_payment_return_url = fields.Char('Payment Return Url', required=True, default='Dummy')

    @api.model
    def enable_b2c_reset_password(self):
        """ Enable sign up and reset password on default website """
        website = self.env.ref('website.default_website', raise_if_not_found=False)
        if website:
            website.auth_signup_uninvited = 'b2c'

        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('auth_signup.invitation_scope', 'b2c')
        ICP.set_param('auth_signup.reset_password', True)


class WebsiteRewrite(models.Model):
    _inherit = 'website.rewrite'

    def _set_vsf_tags(self):
        for website_rewrite in self:
            tags = 'WR%s' % website_rewrite.id
            website_rewrite._vsf_request_cache_invalidation(tags)

    def _vsf_request_cache_invalidation(self, tags_list):
        url = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_url')
        key = self.env['ir.config_parameter'].sudo().get_param('vsf_cache_invalidation_key')
        tags = tags_list

        # Make the GET request to the /cache-invalidate
        requests.get(url, params={'key': key, 'tag': tags})

    def write(self, vals):
        res = super(WebsiteRewrite, self).write(vals)
        self._set_vsf_tags()
        return res

    def unlink(self):
        self._set_vsf_tags()
        return super(WebsiteRewrite, self).unlink()
