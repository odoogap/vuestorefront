# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.address import (
    AddressEnum as VSFAddressEnum,
    AddressFilterInput as VSFAddressFilterInput,
    AddressQuery as VSFAddressQuery,
    AddAddressInput as VSFAddAddressInput,
    DeleteAddressInput as VSFDeleteAddressInput,
    SelectAddressInput as VSFSelectAddressInput,
    UpdateAddressInput as VSFUpdateAddressInput,
    AddAddress as VSFAddAddress,
    UpdateAddress as VSFUpdateAddress,
    DeleteAddress as VSFDeleteAddress,
    SelectAddress as VSFSelectAddress,
    AddressMutation as VSFAddressMutation,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaPartner as Partner,
)


class AddressQuery(VSFAddressQuery):
    addresses = graphene.List(
        graphene.NonNull(Partner),
        filter=graphene.Argument(VSFAddressFilterInput, default_value={})
    )

    @staticmethod
    def resolve_addresses(self, info, filter):
        res = VSFAddressQuery.resolve_addresses(self, info, filter)
        return res


class AddAddress(VSFAddAddress):
    class Arguments:
        type = VSFAddressEnum(required=True)
        address = VSFAddAddressInput()

    Output = Partner

    @staticmethod
    def mutate(self, info, type, address):
        res = VSFAddAddress.mutate(self, info, type, address)
        return res


class UpdateAddress(VSFUpdateAddress):
    class Arguments:
        address = VSFUpdateAddressInput()

    Output = Partner

    @staticmethod
    def mutate(self, info, address):
        res = VSFUpdateAddress.mutate(self, info, address)
        return res


class DeleteAddress(VSFDeleteAddress):
    class Arguments:
        address = VSFDeleteAddressInput()

    result = graphene.Boolean()

    @staticmethod
    def mutate(self, info, address):
        res = VSFDeleteAddress.mutate(self, info, address)
        return res


class SelectAddress(VSFSelectAddress):
    class Arguments:
        type = VSFAddressEnum(required=True)
        address = VSFSelectAddressInput()

    Output = Partner

    @staticmethod
    def mutate(self, info, type, address):
        res = VSFSelectAddress.mutate(self, info, type, address)
        return res


class AddressMutation(VSFAddressMutation):
    add_address = AddAddress.Field(description='Add new billing or shipping address and set it on the shopping cart.')
    update_address = UpdateAddress.Field(
        description="Update a billing or shipping address and set it on the shopping cart."
    )
    delete_address = DeleteAddress.Field(description='Delete a billing or shipping address.')
    select_address = SelectAddress.Field(
        description="Select a billing or shipping address to be used on the shopping cart."
    )
