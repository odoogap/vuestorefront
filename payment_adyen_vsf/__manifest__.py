# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    # Application Information
    'name': 'Adyen Payment Acquirer to VSF',
    'category': 'Accounting/Payment Acquirers',
    'version': '15.0.1.0.0',
    'summary': 'Adyen Payment Acquirer: Adapting Adyen to VSF',

    # Author
    'author': "OdooGap",
    'website': "https://www.odoogap.com/",
    'maintainer': 'OdooGap',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'payment',
        'payment_adyen'
    ],

    # Views
    'data': [
        # 'data/payment_acquirer_data.xml',
        # 'data/mail_channel_data.xml',
        # 'views/payment_adyen_templates.xml',
        # 'views/payment_views.xml',
    ],

    # Technical
    'installable': True,
    'application': False,
    'auto_install': False,
}
