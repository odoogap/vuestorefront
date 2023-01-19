# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import markdown

from odoo import api, models, _


class MarkdownConverter(models.AbstractModel):
    _name = "ir.qweb.field.markdown"
    _description = "Qweb Field Markdown"
    _inherit = "ir.qweb.field"

    @api.model
    def value_to_html(self, value, options):
        return markdown.markdown(value)
