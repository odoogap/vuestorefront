# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vsf_payment_return_url = fields.Char('Payment Return Url', related='website_id.vsf_payment_return_url',
                                         readonly=False, required=True)
    vsf_cache_invalidation_key = fields.Char('Cache Invalidation Key', required=True)
    vsf_cache_invalidation_url = fields.Char('Cache Invalidation Url', required=True)
    vsf_mailing_list_id = fields.Many2one('mailing.list', 'Newsletter', domain=[('is_public', '=', True)])

    # VSF Images
    vsf_image_quality = fields.Integer('Quality', required=True)
    vsf_image_background_rgb = fields.Char('Background RGB', required=True)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            vsf_cache_invalidation_key=ICP.get_param('vsf_cache_invalidation_key'),
            vsf_cache_invalidation_url=ICP.get_param('vsf_cache_invalidation_url'),
            vsf_mailing_list_id=int(ICP.get_param('vsf_mailing_list_id', 0)),
            vsf_image_quality=int(ICP.get_param('vsf_image_quality', 100)),
            vsf_image_background_rgb=ICP.get_param('vsf_image_background_rgb', '(255, 255, 255)'),
        )
        return res

    def set_values(self):
        if self.vsf_image_quality < 0 or self.vsf_image_quality > 100:
            raise ValidationError(_('Invalid image quality percentage.'))

        super(ResConfigSettings, self).set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('vsf_cache_invalidation_key', self.vsf_cache_invalidation_key)
        ICP.set_param('vsf_cache_invalidation_url', self.vsf_cache_invalidation_url)
        ICP.set_param('vsf_mailing_list_id', self.vsf_mailing_list_id.id)
        ICP.set_param('vsf_image_quality', self.vsf_image_quality)
        ICP.set_param('vsf_image_background_rgb', self.vsf_image_background_rgb)
