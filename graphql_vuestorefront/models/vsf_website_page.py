# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class VsfWebsitePage(models.Model):
    _name = 'vsf.website.page'
    _inherit = [
        'website.published.multi.mixin',
        'website.searchable.mixin',
    ]
    _description = 'VSF Website Page'
    _order = 'website_id'

    def _default_content(self):
        return '<p class="o_default_snippet_text">' + _("Start writing here...") + '</p>'

    name = fields.Char(string='Page Name', translate=True, required=True)
    url = fields.Char(string='Page URL', translate=True)
    website_id = fields.Many2one('website', string="Website")
    date_publish = fields.Datetime('Publishing Date')
    content = fields.Text(string='Content', default=_default_content, translate=True)

    page_type = fields.Selection(selection=[
        ('static', 'Static Page'), ('products', 'Products Page')
    ], string='Page Type', default='static', required=True)

    product_tmpl_ids = fields.Many2many(
        'product.template', 'product_template_vsf_website_page_rel', 'vsf_page_id', 'product_tmpl_id',
        string='Product Templates'
    )
    public_categ_ids = fields.Many2many(
        'product.public.category', 'product_public_category_vsf_website_page_rel', 'vsf_page_id', 'public_categ_id',
        string='Public Categories'
    )
