# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic

from odoo.addons.graphql_vuestorefront.schemas.payment import (
    PaymentQuery as VSFPaymentQuery,
    MakeGiftCardPayment as VSFMakeGiftCardPayment,
    PaymentMutation as VSFPaymentMutation,
    AdyenProviderInfoResult as VSFAdyenProviderInfoResult,
    AdyenPaymentMethodsResult as VSFAdyenPaymentMethodsResult,
    AdyenTransactionResult as VSFAdyenTransactionResult,
    AdyenPaymentsResult as VSFAdyenPaymentsResult,
    AdyenPaymentDetailsResult as VSFAdyenPaymentDetailsResult,
    AdyenProviderInfo as VSFAdyenProviderInfo,
    AdyenPaymentMethods as VSFAdyenPaymentMethods,
    AdyenTransaction as VSFAdyenTransaction,
    AdyenPayments as VSFAdyenPayments,
    AdyenPaymentDetails as VSFAdyenPaymentDetails,
    AdyenPaymentMutation as VSFAdyenPaymentMutation,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaPaymentProvider as PaymentProvider,
    ClaPaymentTransaction as PaymentTransaction,
)
from odoo.addons.graphql_cla.schemas.shop import Cart, CartData


class PaymentQuery(VSFPaymentQuery):
    payment_provider = graphene.Field(
        PaymentProvider,
        required=True,
        id=graphene.Int(),
    )
    payment_providers = graphene.List(
        graphene.NonNull(PaymentProvider),
    )
    payment_transaction = graphene.Field(
        PaymentTransaction,
        required=True,
        id=graphene.Int(default_value=None),
        reference=graphene.String(default_value=None)
    )
    payment_confirmation = graphene.Field(
        Cart,
    )

    @staticmethod
    def resolve_payment_provider(self, info, id):
        res = VSFPaymentQuery.resolve_payment_provider(self, info, id)
        return res

    @staticmethod
    def resolve_payment_providers(self, info):
        res = VSFPaymentQuery.resolve_payment_providers(self, info)
        return res

    @staticmethod
    def resolve_payment_transaction(self, info, id, reference):
        res = VSFPaymentQuery.resolve_payment_transaction(self, info, id, reference)
        return res

    @staticmethod
    def resolve_payment_confirmation(self, info):
        res = VSFPaymentQuery.resolve_payment_confirmation(self, info)
        return res


class MakeGiftCardPayment(VSFMakeGiftCardPayment):
    done = graphene.Boolean()

    @staticmethod
    def mutate(self, info):
        res = VSFMakeGiftCardPayment.mutate(self, info)
        return res


class PaymentMutation(VSFPaymentMutation):
    make_gift_card_payment = MakeGiftCardPayment.Field(description='Pay the order only with gift card.')


# -------------------------------- #
#           Adyen Payment          #
# -------------------------------- #

class AdyenProviderInfo(VSFAdyenProviderInfo):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = VSFAdyenProviderInfoResult

    @staticmethod
    def mutate(self, info, provider_id):
        res = VSFAdyenProviderInfo.mutate(self, info, provider_id)
        return res


class AdyenPaymentMethods(VSFAdyenPaymentMethods):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = VSFAdyenPaymentMethodsResult

    @staticmethod
    def mutate(self, info, provider_id):
        res = VSFAdyenPaymentMethods.mutate(self, info, provider_id)
        return res


class AdyenTransaction(VSFAdyenTransaction):
    class Arguments:
        provider_id = graphene.Int(required=True)

    Output = VSFAdyenTransactionResult

    @staticmethod
    def mutate(self, info, provider_id):
        res = VSFAdyenTransaction.mutate(self, info, provider_id)
        return res


class AdyenPayments(VSFAdyenPayments):
    class Arguments:
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        access_token = graphene.String(required=True)
        payment_method = generic.GenericScalar(required=True, description='Return state.data.paymentMethod')
        browser_info = generic.GenericScalar(required=True, description='Return state.data.browserInfo')

    Output = VSFAdyenPaymentsResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference, access_token, payment_method, browser_info):
        res = VSFAdyenPayments.mutate(self, info, provider_id, transaction_reference, access_token, payment_method, browser_info)
        return res


class AdyenPaymentDetails(VSFAdyenPaymentDetails):
    class Arguments:
        provider_id = graphene.Int(required=True)
        transaction_reference = graphene.String(required=True)
        payment_details = generic.GenericScalar(required=True, description='Return state.data')

    Output = VSFAdyenPaymentDetailsResult

    @staticmethod
    def mutate(self, info, provider_id, transaction_reference, payment_details):
        res = VSFAdyenPaymentDetails.mutate(self, info, provider_id, transaction_reference, payment_details)
        return res


class AdyenPaymentMutation(VSFAdyenPaymentMutation):
    adyen_provider_info = AdyenProviderInfo.Field(description='Get Adyen Provider Info.')
    adyen_payment_methods = AdyenPaymentMethods.Field(description='Get Adyen Payment Methods.')
    adyen_transaction = AdyenTransaction.Field(description='Create Adyen Transaction')
    adyen_payments = AdyenPayments.Field(description='Make Adyen Payment request.')
    adyen_payment_details = AdyenPaymentDetails.Field(description='Submit the Adyen Payment Details.')
