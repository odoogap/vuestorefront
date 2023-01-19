# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Web widget Markdown",
    "summary": """
        Add support of markdown content into an Odoo widget form.
    """,
    "description": """
        Allow the use of the widget markdown to display markdown content into Odoo views 
        in render mode and a markdown Editor in edit mode thanks to easyMDE Javascript library
    """,
    'author': 'ERPGap',
    'website': 'https://www.erpgap.com/',
    "category": "web",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "web"],
    "data": [],
    "qweb": [],
    "assets": {
        "web.assets_backend": [
            "/web_widget_markdown/static/src/js/web_markdown.js"
        ],
        "web.assets_qweb": [
            "/web_widget_markdown/static/src/xml/qweb_template.xml",
        ],
    },
    "auto_install": False,
    "installable": True,
}
