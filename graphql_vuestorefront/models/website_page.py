# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class WebsitePage(models.Model):
    _inherit = 'website.page'

    def _default_content(self):
        return '<p class="o_default_snippet_text">' + _("Start writing here...") + '</p>'

    url = fields.Char(string='Page URL', translate=True)
    website_id = fields.Many2one('website', string="Website")
    content = fields.Text(string='Content', default=_default_content, translate=True)
