# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    # Application Information
    'name': 'Stripe Payment Acquirer to VSF',
    'category': 'Accounting/Payment Acquirers',
    'version': '17.0.1.0.0',
    'summary': 'Stripe Payment Acquirer: Adapting Stripe to VSF',

    # Author
    'author': "ERPGAP",
    'website': "https://www.erpgap.com/",
    'maintainer': 'ERPGAP',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'payment',
        'payment_stripe',
    ],

    # Views
    'data': [
        'views/stripe_template.xml',
        'data/website_data.xml',
    ],

    # Assets
    'assets': {
        'web.assets_frontend': [
            'payment_stripe_vsf/static/src/stripe.js'
        ]
    },

    # Technical
    'installable': True,
    'application': False,
    'auto_install': False,
}
