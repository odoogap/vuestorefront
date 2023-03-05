# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError

from odoo import _
from odoo.http import request
from odoo.addons.graphql_vuestorefront.schemas.objects import Partner


def get_partner(env, partner_id, order, website):
    if not order:
        raise GraphQLError(_('Shopping cart not found.'))

    ResPartner = env['res.partner'].with_context(show_address=1).sudo()
    partner = ResPartner.browse(partner_id)

    # Is public user
    if not order.partner_id.user_ids or order.partner_id.id == website.user_id.sudo().partner_id.id:
        partner_id = order.partner_id.id
    else:
        partner_id = env.user.partner_id.commercial_partner_id.id

    # Addresses that belong to this user
    shippings = ResPartner.search([
        ("id", "child_of", partner_id),
        '|', ("type", "in", ["delivery", "invoice"]),
        ("id", "=", partner_id)
    ])

    # Validate if the address exists and if the user has access to this address
    if not partner or not partner.exists() or partner.id not in shippings.ids:
        raise GraphQLError(_('Address not found.'))

    return partner


class AddressEnum(graphene.Enum):
    Billing = 'invoice'
    Shipping = 'delivery'


class AddressFilterInput(graphene.InputObjectType):
    address_type = graphene.List(AddressEnum)


class AddressQuery(graphene.ObjectType):
    addresses = graphene.List(
        graphene.NonNull(Partner),
        filter=graphene.Argument(AddressFilterInput, default_value={})
    )

    @staticmethod
    def resolve_addresses(self, info, filter):
        env = info.context["env"]
        ResPartner = env['res.partner'].with_context(show_address=1).sudo()
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        if not order:
            raise GraphQLError(_('Shopping cart not found.'))

        # Is public user
        if not order.partner_id.user_ids or order.partner_id.id == website.user_id.sudo().partner_id.id:
            partner_id = order.partner_id.id
        else:
            partner_id = env.user.partner_id.commercial_partner_id.id

        # Get all addresses of a specific addressType - delivery or/and shipping
        if filter.get('address_type'):
            types = [address_type.value for address_type in filter.get('address_type', [])]

            domain = [
                ("id", "child_of", partner_id),
                ("type", "in", types),
            ]
        # Get all addresses with addressType delivery and invoice
        else:
            domain = [
                ("id", "child_of", partner_id),
                '|', ("type", "in", ['delivery', 'invoice']),
                ("id", "=", partner_id),
            ]

        return ResPartner.search(domain, order='id desc')


class AddAddressInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    street = graphene.String(required=True)
    street2 = graphene.String()
    zip = graphene.String(required=True)
    city = graphene.String()
    state_id = graphene.Int()
    country_id = graphene.Int(required=True)
    phone = graphene.String(required=True)
    email = graphene.String()


class DeleteAddressInput(graphene.InputObjectType):
    id = graphene.Int(required=True)


class SelectAddressInput(graphene.InputObjectType):
    id = graphene.Int(required=True)


class UpdateAddressInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    street = graphene.String()
    street2 = graphene.String()
    zip = graphene.String()
    city = graphene.String()
    state_id = graphene.Int()
    country_id = graphene.Int()
    phone = graphene.String()
    email = graphene.String()


class AddAddress(graphene.Mutation):
    class Arguments:
        type = AddressEnum(required=True)
        address = AddAddressInput()

    Output = Partner

    @staticmethod
    def mutate(self, info, type, address):
        env = info.context["env"]
        ResPartner = env['res.partner'].sudo().with_context(tracking_disable=True)
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        if not order:
            raise GraphQLError(_('Shopping cart not found.'))

        values = {
            'name': address.get('name'),
            'street': address.get('street'),
            'street2': address.get('street2'),
            'phone': address.get('phone'),
            'zip': address.get('zip'),
            'city': address.get('city'),
            'state_id': address.get('state_id', False),
            'country_id': address.get('country_id', False),
            'email': address.get('email', False),
        }

        partner_id = order.partner_id.id

        # Check public user
        if partner_id == website.user_id.sudo().partner_id.id:
            # Create main contact
            values['type'] = 'contact'
            partner_id = ResPartner.create(values).id
            order.partner_id = partner_id

        values['type'] = type.value
        values['parent_id'] = partner_id

        # Create the new shipping or invoice address
        partner = ResPartner.create(values)

        # Update order with the new shipping or invoice address
        if values['type'] == 'invoice':
            order.partner_invoice_id = partner.id
        elif values['type'] == 'delivery':
            order.partner_shipping_id = partner.id

        # Trigger the change of fiscal position when the shipping address is modified
        order._compute_fiscal_position_id()

        return partner


class UpdateAddress(graphene.Mutation):
    class Arguments:
        address = UpdateAddressInput(required=True)

    Output = Partner

    @staticmethod
    def mutate(self, info, address):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        partner = get_partner(env, address['id'], order, website)

        values = {}
        if address.get('name'):
            values.update({'name': address['name']})
        if address.get('street'):
            values.update({'street': address['street']})
        if address.get('street2'):
            values.update({'street2': address['street2']})
        if address.get('phone'):
            values.update({'phone': address['phone']})
        if address.get('zip'):
            values.update({'zip': address['zip']})
        if address.get('city'):
            values.update({'city': address['city']})
        if address.get('state_id'):
            values.update({'state_id': address['state_id']})
        if address.get('country_id'):
            values.update({'country_id': address['country_id']})

            # Trigger the change of fiscal position when the shipping address is modified
            order._compute_fiscal_position_id()

        if address.get('email'):
            values.update({'email': address['email']})

        if values:
            partner.write(values)

        return partner


class DeleteAddress(graphene.Mutation):
    class Arguments:
        address = DeleteAddressInput()

    result = graphene.Boolean()

    @staticmethod
    def mutate(self, info, address):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        partner = get_partner(env, address['id'], order, website)

        if not partner.parent_id:
            raise GraphQLError(_("You can't delete the primary address."))

        if order.partner_invoice_id.id == partner.id:
            order.partner_invoice_id = partner.parent_id.id

        if order.partner_shipping_id.id == partner.id:
            order.partner_shipping_id = partner.parent_id.id

        # Archive address, safer than delete since this address could be in use by other object
        partner.active = False

        # Trigger the change of fiscal position when the shipping address is modified
        order._compute_fiscal_position_id()

        return DeleteAddress(result=True)


class SelectAddress(graphene.Mutation):
    class Arguments:
        type = AddressEnum(required=True)
        address = SelectAddressInput()

    Output = Partner

    @staticmethod
    def mutate(self, info, type, address):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        partner = get_partner(env, address['id'], order, website)

        # Update order with the new shipping or invoice address
        if type.value == 'invoice':
            order.partner_invoice_id = partner.id
        elif type.value == 'delivery':
            order.partner_shipping_id = partner.id

        # Trigger the change of fiscal position when the shipping address is modified
        order._compute_fiscal_position_id()

        return partner


class AddressMutation(graphene.ObjectType):
    add_address = AddAddress.Field(description='Add new billing or shipping address and set it on the shopping cart.')
    update_address = UpdateAddress.Field(description="Update a billing or shipping address and set it on the shopping "
                                                     "cart.")
    delete_address = DeleteAddress.Field(description='Delete a billing or shipping address.')
    select_address = SelectAddress.Field(description="Select a billing or shipping address to be used on the shopping "
                                                     "cart.")
