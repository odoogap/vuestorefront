# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.graphql_vuestorefront.schemas.contact_us import (
    ContactUsParams as VSFContactUsParams,
    ContactUs as VSFContactUs,
    ContactUsMutation as VSFContactUsMutation,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaLead as Lead,
)


class ContactUs(VSFContactUs):
    class Arguments:
        contactus = VSFContactUsParams()

    Output = Lead

    @staticmethod
    def mutate(self, info, contactus):
        res = VSFContactUs.mutate(self, info, contactus)
        return res


class ContactUsMutation(VSFContactUsMutation):
    contact_us = ContactUs.Field(description='Creates a new lead with the contact information.')
