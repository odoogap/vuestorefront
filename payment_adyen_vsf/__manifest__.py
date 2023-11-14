# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    # Application Information
    'name': 'Adyen Payment Acquirer to VSF',
    'category': 'Accounting/Payment Acquirers',
    'version': '17.0.1.0.0',
    'summary': 'Adyen Payment Acquirer: Adapting Adyen to VSF',

    # Author
    'author': "ERPGAP",
    'website': "https://www.erpgap.com/",
    'maintainer': 'ERPGAP',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'payment',
        'payment_adyen'
    ],

    # Views
    'data': [],

    # Technical
    'installable': True,
    'application': False,
    'auto_install': False,
}
