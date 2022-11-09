# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# Endpoints of the API.
# See https://docs.adyen.com/api-explorer/#/CheckoutService/v67/overview for Checkout API
# See https://docs.adyen.com/api-explorer/#/Recurring/v49/overview for Recurring API
API_ENDPOINT_VERSIONS = {
    '/disable': 49,                 # Recurring API
    '/payments': 67,                # Checkout API
    '/payments/details': 67,        # Checkout API
    '/payments/{}/refunds': 67,     # Checkout API
    '/paymentMethods': 67,          # Checkout API
}

# Adyen-specific mapping of currency codes in ISO 4217 format to the number of decimals.
# Only currencies for which Adyen does not follow the ISO 4217 norm are listed here.
# See https://docs.adyen.com/development-resources/currency-codes
CURRENCY_DECIMALS = {
    'BHD': 3,
    'CLP': 2,
    'CVE': 0,
    'DJF': 0,
    'GNF': 0,
    'IDR': 0,
    'ISK': 2,
    'JOD': 3,
    'JPY': 0,
    'KMF': 0,
    'KRW': 0,
    'KWD': 3,
    'LYD': 3,
    'OMR': 3,
    'PYG': 0,
    'RWF': 0,
    'TND': 3,
    'UGX': 0,
    'VND': 0,
    'VUV': 0,
    'XAF': 0,
    'XOF': 0,
    'XPF': 0,
    'USD': 2,
    'EUR': 2,
    'SEK': 2,
    'DKK': 2,
}

# Mapping of transaction states to Adyen result codes.
# See https://docs.adyen.com/checkout/payment-result-codes for the exhaustive list of result codes.
RESULT_CODES_MAPPING = {
    'pending': (
        'ChallengeShopper', 'IdentifyShopper', 'Pending', 'PresentToShopper', 'Received',
        'RedirectShopper'
    ),
    'done': ('Authorised',),
    'cancel': ('Cancelled',),
    'error': ('Error',),
    'refused': ('Refused',),
}
