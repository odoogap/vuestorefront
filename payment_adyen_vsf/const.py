# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.payment_adyen.const import API_ENDPOINT_VERSIONS, CURRENCY_DECIMALS, RESULT_CODES_MAPPING

# Endpoints of the API.
# See https://docs.adyen.com/api-explorer/#/CheckoutService/v67/overview for Checkout API
# See https://docs.adyen.com/api-explorer/#/Recurring/v49/overview for Recurring API
API_ENDPOINT_VERSIONS.update({
    '/payments/{}/reversals': 67,   # Checkout API
})

# Adyen-specific mapping of currency codes in ISO 4217 format to the number of decimals.
# Only currencies for which Adyen does not follow the ISO 4217 norm are listed here.
# See https://docs.adyen.com/development-resources/currency-codes
CURRENCY_DECIMALS.update({
    "BHD": 3,
    "DJF": 0,
    "GNF": 0,
    "JOD": 3,
    "JPY": 0,
    "KMF": 0,
    "KRW": 0,
    "KWD": 3,
    "LYD": 3,
    "OMR": 3,
    "PYG": 0,
    "RWF": 0,
    "TND": 3,
    "UGX": 0,
    "VND": 0,
    "VUV": 0,
    "XAF": 0,
    "XOF": 0,
    "XPF": 0,
    "USD": 2,
    "EUR": 2,
    "SEK": 2,
    "DKK": 2,
})
