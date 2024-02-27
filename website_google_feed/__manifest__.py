# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Website Google Feed',
    'category': 'Website',
    'version': '17.0.1.0.0',
    'summary': 'Website Google Feed',
    'author': "Odoo Gap",
    'website': "https://www.erpgap.com/",
    'maintainer': 'Odoo Gap',
    'license': 'LGPL-3',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/website_feed.xml',
    ],
    'installable': False,
    'application': True,
    'auto_install': False,
}
