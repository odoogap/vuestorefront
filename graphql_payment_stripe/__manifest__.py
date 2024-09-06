# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Graphql Payment Stripe',
    'version': '17.0.0.0.1',
    'summary': 'Graphql Payment Stripe',
    'description': """Graphql Payment Stripe Integration""",
    'category': 'Website',
    'license': 'LGPL-3',
    'author': 'ERPGAP',
    'website': 'https://www.erpgap.com/',
    'depends': [
        'graphql_vuestorefront',
        'payment_stripe'
    ],
    'assets': {
        'web.assets_frontend': [
            'graphql_payment_stripe/static/src/stripe.js'
        ]
    },
    'installable': True,
    'auto_install': False,
}
