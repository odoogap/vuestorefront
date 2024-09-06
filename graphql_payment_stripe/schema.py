# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_payment_stripe.schemas import payment

from odoo.addons.graphql_vuestorefront.schema import (
    Query as VSFQuery,
    Mutation as VSFMutation,
)

class Mutation(
    VSFMutation,
    payment.StripePaymentMutation,
):
    pass


schema = graphene.Schema(
    query=VSFQuery,
    mutation=Mutation,
)
