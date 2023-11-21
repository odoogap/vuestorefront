# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.addons.graphql_base import OdooObjectType
from odoo.addons.graphql_vuestorefront.schemas import (
    country, category, product, order,
    invoice, contact_us, user_profile, sign,
    address, wishlist, shop, payment,
    mailing_list, website,
)
import logging

_logger = logging.getLogger(__name__)


class GraphQLType(OdooObjectType):
    """ Base class for all GraphQL types"""
    _odoo_model = False


class GraphQLQuery(graphene.ObjectType):
    """ Base class for all GraphQL queries"""
    _odoo_model = False


class Mutation(
    OdooObjectType,
    contact_us.ContactUsMutation,
    user_profile.UserProfileMutation,
    sign.SignMutation,
    address.AddressMutation,
    wishlist.WishlistMutation,
    shop.ShopMutation,
    payment.PaymentMutation,
    payment.AdyenPaymentMutation,
    mailing_list.NewsletterSubscribeMutation,
    order.OrderMutation,
):
    pass


class SchemaBuilder(object):

    def __init__(self, env):
        self._env = env

    def load_schema(self):
        # register all simple fields
        cls_list = [
            OdooObjectType,
            country.CountryQuery,
            category.CategoryQuery,
            product.ProductQuery,
            order.OrderQuery,
            invoice.InvoiceQuery,
            user_profile.UserProfileQuery,
            address.AddressQuery,
            wishlist.WishlistQuery,
            shop.ShoppingCartQuery,
            payment.PaymentQuery,
            mailing_list.MailingContactQuery,
            mailing_list.MailingListQuery,
            website.WebsiteQuery,
        ]
        type_list = [
                country.CountryList, category.CategoryList, product.ProductList,
                product.ProductVariantData, order.OrderList,
                invoice.InvoiceList, wishlist.WishlistData, shop.CartData,
                mailing_list.MailingContactList,
                mailing_list.MailingListList
        ]
        for cls in GraphQLType.__subclasses__():
            _logger.info('GraphQL Class: %s' % cls.__name__)
            if cls._odoo_model:
                model_name = cls._odoo_model
                # add Type class
                fields = self._env[model_name].fields_get()
                resolver_dict, fields_dict = self._get_properties_dict(fields)
                cls_type = type(cls.__name__, (GraphQLType, cls.__class__), fields_dict)
                # Add resolver methods
                for field_name, resolver_method in resolver_dict.items():
                    setattr(
                        cls_type,
                        f"resolve_{field_name}",
                        classmethod(resolver_method)
                    )
                type_list.append(cls_type)

                # add Query class
                cls_query = next((x for x in GraphQLQuery.__subclasses__() if getattr(x, '_odoo_model', None) == model_name), None)
                if not cls_query:
                    raise Exception('Query class not found for model %s' % model_name)
                setattr(
                    cls_query, cls.__name__.lower(),
                    graphene.Field(cls_type, required=True, id=graphene.Int(default_value=None))
                )
                # Add resolver query id method
                setattr(cls_query, f"resolve_{cls.__name__.lower()}", classmethod(self._generate_resolver_query_method(model_name)))
                cls_list.append(cls_query)

        Query = type('Query', tuple(cls_list), {})
        return graphene.Schema(
            query=Query,
            mutation=Mutation,
            types=type_list
        )

    def _get_properties_dict(self, fields):
        fields_dict = {}
        resolver_dict = {}
        for field_name, fld_properties in filter(lambda item: item[1]['type'] in (
                'char', 'html', 'text', 'integer', 'selection', 'float', 'monetary'), fields.items()):
            if fld_properties['type'] in ('char', 'html', 'text', 'selection'):
                fields_dict[field_name] = graphene.String(required=False)
            elif fld_properties['type'] in ('float', 'monetary'):
                fields_dict[field_name] = graphene.Float()
            elif fld_properties['type'] == 'integer':
                fields_dict[field_name] = graphene.Int()

            resolver_dict[field_name] = self._generate_resolver_method(field_name)

        return resolver_dict, fields_dict

    def _generate_resolver_method(self, field_name):
        @staticmethod
        def resolver_method(parent, info, field_name=field_name):
            return getattr(parent, field_name, None)

        return resolver_method

    def _generate_resolver_query_method(self, model_name):
        @staticmethod
        def id_resolver_method(parent, info, id, model_name=model_name):
            return info.context['env'][model_name].search([('id', '=', id)], limit=1)

        return id_resolver_method
