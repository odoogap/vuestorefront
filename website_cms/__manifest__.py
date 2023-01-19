# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Website CMS',
    'version': '15.0.1.0.0',
    'category': 'Website',
    'license': 'LGPL-3',
    'summary': 'Website CMS',
    'description': """
Website CMS - Publish Content on VSF Website
============================================

""",
    'author': 'ERPGap',
    'website': 'https://www.erpgap.com/',
    'depends': [
        'website',
        'web_widget_markdown',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/website_cms_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
