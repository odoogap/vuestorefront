# -*- coding: utf-8 -*-
# Copyright 2021 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import uuid
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vsf_payment_success_return_url = fields.Char(
        'Payment Success Return Url', related='website_id.vsf_payment_success_return_url', readonly=False,
        required=True
    )
    vsf_payment_error_return_url = fields.Char(
        'Payment Error Return Url', related='website_id.vsf_payment_error_return_url', readonly=False,
        required=True
    )
    vsf_cache_invalidation = fields.Boolean('Cache Invalidation')
    vsf_cache_invalidation_key = fields.Char('Cache Invalidation Key', required=True)
    vsf_cache_invalidation_url = fields.Char('Cache Invalidation Url', required=True)
    vsf_mailing_list_id = fields.Many2one('mailing.list', 'Newsletter', domain=[('is_public', '=', True)],
                                          related='website_id.vsf_mailing_list_id', readonly=False, required=True)
    vsf_debug_mode = fields.Boolean('Debug Mode')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            vsf_cache_invalidation=ICP.get_param('vsf_cache_invalidation'),
            vsf_cache_invalidation_key=ICP.get_param('vsf_cache_invalidation_key'),
            vsf_cache_invalidation_url=ICP.get_param('vsf_cache_invalidation_url'),
            vsf_debug_mode=ICP.get_param('vsf_debug_mode'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('vsf_cache_invalidation', self.vsf_cache_invalidation)
        ICP.set_param('vsf_cache_invalidation_key', self.vsf_cache_invalidation_key)
        ICP.set_param('vsf_cache_invalidation_url', self.vsf_cache_invalidation_url)
        ICP.set_param('vsf_debug_mode', self.vsf_debug_mode)

    @api.model
    def create_vsf_cache_invalidation_key(self):
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('vsf_cache_invalidation_key', str(uuid.uuid4()))
