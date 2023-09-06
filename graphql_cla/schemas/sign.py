# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.sign import (
    Login as VSFLogin,
    Logout as VSFLogout,
    Register as VSFRegister,
    ResetPassword as VSFResetPassword,
    ChangePassword as VSFChangePassword,
    UpdatePassword as VSFUpdatePassword,
    SignMutation as VSFSignMutation,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaUser as User,
)


class Login(VSFLogin):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        subscribe_newsletter = graphene.Boolean(default_value=False)

    Output = User

    @staticmethod
    def mutate(self, info, email, password, subscribe_newsletter):
        res = VSFLogin.mutate(self, info, email, password, subscribe_newsletter)
        return res


class Logout(VSFLogout):

    Output = graphene.Boolean

    @staticmethod
    def mutate(self, info):
        res = VSFLogout.mutate(self, info)
        return res


class Register(VSFRegister):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        subscribe_newsletter = graphene.Boolean(default_value=False)

    Output = User

    @staticmethod
    def mutate(self, info, name, email, password, subscribe_newsletter):
        res = VSFRegister.mutate(self, info, name, email, password, subscribe_newsletter)
        return res


class ResetPassword(VSFResetPassword):
    class Arguments:
        email = graphene.String(required=True)

    Output = User

    @staticmethod
    def mutate(self, info, email):
        res = VSFResetPassword.mutate(self, info, email)
        return res


class ChangePassword(VSFChangePassword):
    class Arguments:
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    Output = User

    @staticmethod
    def mutate(self, info, token, new_password):
        res = VSFChangePassword.mutate(self, info, token, new_password)
        return res


class UpdatePassword(VSFUpdatePassword):
    class Arguments:
        current_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    Output = User

    @staticmethod
    def mutate(self, info, current_password, new_password):
        res = VSFUpdatePassword.mutate(self, info, current_password, new_password)
        return res


class SignMutation(VSFSignMutation):
    login = Login.Field(description='Authenticate user with email and password and retrieves token.')
    logout = Logout.Field(description='Logout user')
    register = Register.Field(description='Register a new user with email, name and password.')
    reset_password = ResetPassword.Field(description="Send change password url to user's email.")
    change_password = ChangePassword.Field(description="Set new user's password with the token from the change "
                                                       "password url received in the email.")
    update_password = UpdatePassword.Field(description="Update user password.")
