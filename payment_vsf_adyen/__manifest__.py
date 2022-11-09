# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# Assets:
#     'https://checkoutshopper-live.adyen.com/checkoutshopper/sdk/4.7.3/adyen.css',
#     'https://checkoutshopper-live.adyen.com/checkoutshopper/sdk/4.7.3/adyen.js',


{
    # Application Information
    'name': 'Adyen Payment Acquirer (New Version)',
    'version': '14.0.1.0.0',
    'summary': 'Payment Acquirer: Adyen Implementation with New Version',
    'description': """Adyen Payment Acquirer""",
    'category': 'Accounting/Payment Acquirers',

    # Author
    'author': "OdooGap",
    'website': 'https://www.odoogap.com/',
    'maintainer': 'OdooGap',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'payment',
        'payment_vsf',
        'payment_adyen',
        'payment_adyen_paybylink',
    ],

    # Views
    'data': [
        'data/payment_acquirer_data.xml',
        'views/payment_views.xml',
    ],

    # Technical
    'application': True,
    'installable': True,
    'auto_install': False,
}
