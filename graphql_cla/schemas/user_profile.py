# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.user_profile import (
    UserProfileQuery as VSFUserProfileQuery,
    UpdateMyAccount as VSFUpdateMyAccount,
    UpdateMyAccountParams as VSFUpdateMyAccountParams,
    UserProfileMutation as VSFUserProfileMutation,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaPartner as Partner,
)


class UserProfileQuery(VSFUserProfileQuery):
    partner = graphene.Field(
        Partner,
        required=True,
    )

    @staticmethod
    def resolve_partner(self, info):
        res = VSFUserProfileQuery.resolve_partner(self, info)
        return res


class UpdateMyAccount(VSFUpdateMyAccount):
    class Arguments:
        myaccount = VSFUpdateMyAccountParams()

    Output = Partner

    @staticmethod
    def mutate(self, info, myaccount):
        res = VSFUpdateMyAccount.mutate(self, info, myaccount)
        return res


class UserProfileMutation(VSFUserProfileMutation):
    update_my_account = UpdateMyAccount.Field(description='Update MyAccount')
