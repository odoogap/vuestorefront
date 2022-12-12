# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, SUPERUSER_ID


def _delete_payment_adyen_og_module(env):
    """
    This module should be removed
    """
    env.cr.execute("DELETE FROM ir_module_module WHERE name = 'payment_adyen_og';")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _delete_payment_adyen_og_module(env)
