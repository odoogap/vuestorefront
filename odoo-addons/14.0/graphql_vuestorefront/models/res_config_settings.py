# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vsf_reset_password_url = fields.Char('Reset Password Url', required=True)
    vsf_payment_return_url = fields.Char('Payment Return Url', required=True)
    vsf_cache_invalidation_key = fields.Char('Cache Invalidation Key', required=True)
    vsf_cache_invalidation_url = fields.Char('Cache Invalidation Url', required=True)
    web_base_url = fields.Char('Web Base Url', required=True)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            vsf_reset_password_url=ICP.get_param('vsf_reset_password_url'),
            vsf_payment_return_url=ICP.get_param('vsf_payment_return_url'),
            vsf_cache_invalidation_key=ICP.get_param('vsf_cache_invalidation_key'),
            vsf_cache_invalidation_url=ICP.get_param('vsf_cache_invalidation_url'),
            web_base_url=ICP.get_param('web.base.url'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('vsf_reset_password_url', self.vsf_reset_password_url)
        ICP.set_param('vsf_payment_return_url', self.vsf_payment_return_url)
        ICP.set_param('vsf_cache_invalidation_key', self.vsf_cache_invalidation_key)
        ICP.set_param('vsf_cache_invalidation_url', self.vsf_cache_invalidation_url)
        ICP.set_param('web.base.url', self.web_base_url)
