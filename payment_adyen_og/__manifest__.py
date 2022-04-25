# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    # Application Information
    'name': 'Adyen Payment Acquirer',
    'category': 'Accounting/Payment Acquirers',
    'version': '15.0.1.0.0',
    'summary': 'Payment Acquirer: Adyen Implementation with form redirection(HPP) method.',

    # Author
    'author': "Odoo Gap",
    'website': "https://www.odoogap.com/",
    'maintainer': 'Odoo Gap',
    'license': 'LGPL-3',

    # Dependencies
    'depends': ['payment'],

    # Views
    'data': ['views/payment_adyen_templates.xml',
             'data/payment_acquirer_data.xml',
             'views/payment_views.xml'],

    # Technical
    'installable': True,
    'application': False,
    'auto_install': False,
}
