# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _
from odoo.http import request
from odoo.osv import expression

from odoo.addons.graphql_vuestorefront.schemas.objects import PaymentAcquirer
from odoo.addons.graphql_vuestorefront.schemas.shop import Cart, CartData
from odoo.addons.website_sale.controllers.main import WebsiteSale, PaymentPortal
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment_adyen.controllers.main import AdyenController


class PaymentQuery(graphene.ObjectType):
    payment_acquirer = graphene.Field(
        PaymentAcquirer,
        required=True,
        id=graphene.Int(),
    )
    payment_acquirers = graphene.List(
        graphene.NonNull(PaymentAcquirer),
    )
    # payment_confirmation = graphene.Field(
    #     Cart,
    # )

    def resolve_payment_acquirer(self, info, id):
        domain = [
            ('id', '=', id),
            ('state', 'in', ['enabled', 'test']),
        ]
        payment_acquirer = info.context["env"]['payment.acquirer'].sudo().search(domain, limit=1)
        if not payment_acquirer:
            raise GraphQLError(_('Payment acquirer does not exist.'))
        return payment_acquirer

    def resolve_payment_acquirers(self, info):
        env = info.context["env"]

        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        domain = expression.AND([
            ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order.company_id.id)],
            ['|', ('website_id', '=', False), ('website_id', '=', website.id)],
            ['|', ('country_ids', '=', False), ('country_ids', 'in', [order.partner_id.country_id.id])]
        ])
        return env['payment.acquirer'].search(domain)

    # ----------------------- #
    #    Needed be Migrate    #
    # ----------------------- #

    # def resolve_payment_confirmation(self, info):
    #     env = info.context["env"]
    #
    #     PaymentTransaction = env['payment.transaction']
    #     Order = env['sale.order']
    #
    #     # Pass in the session the sale_order created in vsf
    #     payment_transaction_id = request.session.get('__payment_tx_ids__')[0]
    #
    #     if payment_transaction_id:
    #
    #         payment_transaction = PaymentTransaction.sudo().search([
    #             ('id', '=', payment_transaction_id)], limit=1)
    #
    #         sale_order_id = payment_transaction.sale_order_ids.ids[0]
    #
    #     if sale_order_id:
    #         order = Order.sudo().search([('id', '=', sale_order_id)], limit=1)
    #
    #         if order.exists():
    #             return CartData(order=order)
    #
    #     raise GraphQLError(_('Cart does not exist'))


def validate_expiry(expiry_month, expiry_year):
    # Validate expiry month and year
    if expiry_month > 12 or expiry_month < 1:
        raise GraphQLError(_('Invalid Month'))

    cc_expiry = '%s / %s' % ("{:02d}".format(expiry_month), expiry_year)

    expiry_date = datetime.strptime(cc_expiry, '%m / %Y').strftime('%Y%m')

    if datetime.now().strftime('%Y%m') > expiry_date:
        raise GraphQLError(_('Invalid Month / Year'))
    return cc_expiry


def prepare_payment_transaction(env, data, payment_acquire, order):
    payment_token = payment_acquire.ogone_s2s_form_process(data)

    # create normal s2s transaction
    transaction = env['payment.transaction'].sudo().create({
        'amount': order.amount_total,
        'acquirer_id': payment_acquire.id,
        'type': 'server2server',
        'currency_id': order.currency_id.id,
        'reference': order.name,
        'payment_token_id': payment_token.id,
        'partner_id': order.partner_id.id,
        'sale_order_ids': [(6, 0, order.ids)]

    })
    return transaction


class SelectPaymentAcquirerResult(graphene.ObjectType):
    form = generic.GenericScalar()


class SelectPaymentAcquirer(graphene.Mutation):
    class Arguments:
        payment_acquire_id = graphene.Int(required=True)

    Output = SelectPaymentAcquirerResult

    @staticmethod
    def mutate(self, info, payment_acquire_id):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        payment_acquirer = env['payment.acquirer'].sudo().search([('id', '=', payment_acquire_id)], limit=1)

        if payment_acquirer:

            # Adyen Payment
            if payment_acquirer.name == 'Adyen':

                return SelectPaymentAcquirerResult(
                    form=AdyenController().adyen_payment_methods(
                        acquirer_id=payment_acquire_id, amount=order.amount_total, currency_id=order.currency_id.id,
                        partner_id=order.partner_id.id
                    )
                )


class MakePaymentResult(graphene.ObjectType):
    result = generic.GenericScalar()


class MakePayment(graphene.Mutation):
    class Arguments:
        payment_acquire_id = graphene.Int(required=True)

    Output = MakePaymentResult

    @staticmethod
    def mutate(self, info, payment_acquire_id):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order()

        # return MakePaymentResult(
        #     form=WebsiteSale().payment_transaction(payment_acquire_id).decode('utf-8')
        # )

        # Create Transaction
        transaction = PaymentPortal().shop_payment_transaction(
            order_id=order.id,
            access_token=order.access_token,
            payment_option_id=payment_acquire_id,
            amount=order.amount_total,
            currency_id=order.currency_id.id,
            partner_id=order.partner_id.id,
            flow='direct',
            tokenization_requested=False,
            landing_route='/shop/payment/validate'
        )

        # payment_method = {
        #     'type': 'scheme',
        #     'number': '4111111145551142',
        #     'expiryMonth': '03',
        #     'expiryYear': '2030',
        #     'holderName': 'John Smith',
        #     'cvc': '737'
        # }

        payment_method = {
            "encryptedCardNumber": "adyenjs_0_1_25$HlMMVTe0J8xtbHpsXJiQGn32PnR0JChVknlMrxpURtZ8LqocOvY21lvM1/e1S6CKmPdrT8LT96vb7XqdMJ0UvWlPyeuJkUVpweMgSUdv+e7E4Tl0JS59qwj+KcfIilZIkh2Rk7Cr4myqRHjoKfKnxQLWbCMqoBR9XGm8uDo4Ebry9cHESHsjiX6nZy8XDoQhmregcotyFGLHZ4hkeyYkPhO/ocCPKKMaG6xCKACe+jgZIQX33mrKi9BE8TKRClAymdhXQVBxfPvXsK/i8Ll9m1ez4XQUVH6LZN+/IAyy2q0rLU171om467CDKemTNjplctmiEjEvenigJTB8s+XQuA==$62vQAoDfK+xKF2NICq9DB7HWSsZsqqrioSBHCgXHRc8Vd5yt7B2imM52GtG5OXxbWqzJxK5kYMv1qLDGpDRjdDhdh32ihyx1Kpga4VHA1MLHqPcEEU3cZIKe7okJiE+gSlWAo4gavnI34/h5kUbhywLQThHarhL3jx+tBUo38K+CdfqIbkW61QRWPK27UI/VPcgfNfUDKM8Hx1WMCk/UoNERBJnOIQBV7FCzgC1T97qR7vwgM0hh5ZquJ3+odtxMyZEjHnluCUMwfvZ3NOVjYgVJbW4pOPf40zWQCoLevffMmIxX/sw38byFEQ1iBqoGWMJDo2EV/3Wvny9t3iOh+/fRIJchgpneMIkdYw3c8/lCaF1qS6RIthtRc9Ua3Y8EZsCUocgiK2dVHRH40oxBlyNZUoCQ7QnfMrdlMeRyQOdtOPlpnoeBkEg+NCAyqlc4xQtNo2nU02+d1AaJTNv2sASTPfnLJcBmWiw1skywLya9qdA7TfVMYnpePpPgYFtO9SgzQI/nnawmpMeJENS3YgwOFhu69UhiMFikBfNlnTlx6ytBfkhiPxFE8guIwH8zR2bNge1fdZJjpV9IdBYNdPURIYVT3Ie8DhBtgJ56cZM9koTArLAfjsdj9hHFZSqK++DNwP0DeEF5Ba1BQElw3SD/bXoQr11Jrsj00kb6tGY+S6ZcPdzP5E+RYdi7ITsYm0G4fWtVp1yZt08fke1DCmc5ThFIgMWVjCoHusKUis3c48voW7p/0X7WhRXcL5XY8A92NFvWrFg/gQusM6H8e+36rCqsVRnjDg8LP+1utsA28tgc",
            "encryptedExpiryMonth": "adyenjs_0_1_25$13XZvAXswsnSJvZwliYlCrVr7OEFC9hS/9tydx7iqPlBi4xtY9FiG9+UI3I9ZIw9PisUEBvk2rLnoB2du2TA56ehyh3ld9lMm0WWwk6fTZEWOjdyhnApRmpkjgOIZk7pKIh3zi4pPeY/sm4+KAGQjn71mNzzRBULsmyngkLv0cTV+IZ3jrPah96yYHKqJNtOgI3NLqoruNcMSihdXthpFPCld+BWLIYGbEVbV+3px1n5zYg8dEDSO1vK8nVzVmdRQOjmfwXiRvXRVdY+bcj6uQYUdJYEIKnZL51qHb1QviAqOqk1mY7xWxSO8kAwFmrHK4vIr1lY5CEaWU+5UGqDcA==$bQp7H7LPeZ5770lhP6+KtwFefulANaxc9qIP3GUK0f0v+NFDUJAY5L37nQkAd7UjdBNulbh5s73/wLKS2JHqEhKooVs1w+8/E4SXbsk1nRVODMW1KDM1h3oGP1dz/5zqeeuSZUE4xVZvw9MN8HJEhB+U8SWP++neaV/wSLSUBclDA0R5qnGWsqlJ8aL61b8uiJwQ43zO1Aa5EGotVF/f23m4vDjis48V0dlZYz1/5omXDhBvE9Ml6Eh1HtYu5L2cTmJzXW8rM2yJTT9azY5tCGB7MNO0OZyvIr6bquUJhZkI9s0NVj0oQlzm7IxNLjJS3WlhrFDY0gggVYJhpDi3LRXV+JUm/r2OBR1fCprO6QRYGXPgxXx2Mg6dFediFwkUwj5HIIHGi9Fl/xf4VBh3yt5A1Zm6ZLUMRluDHpdBM4xxaUnZKFILJ5MSxwiq/e3cdkgfZg76a93QNc8sjSf5ZR7cibFhaV5Hmisbzd00Ayw4DHOKcIC8",
            "encryptedExpiryYear": "adyenjs_0_1_25$Y+GM8fTCMTow6RssD5kSUgZJNRVgBABlh6V28D2D43yhfPYlmUKuulSPuWWjosAG8S9iUrlNkBI+vWoMk0qxd2sKMflxWcWbdbkKOy3/MWG9sGHdZl3e4KlWdxfdmh9K2UlLSxvl6bBBiRAba94R0wGMBaMeML3uXwvys5lEFzbMwt27NHCYHhoOK9VfuuKmQq8VKZ1+IphuAfiKxpnn795WoxvDnCc9FOh9H2hVln4Pj6XusZcieDbAm+nP5Dfq2Lx4t+1lbsoF2vv4YSBO8L7Dt+tn+lvmMbk9SzfLHXrGMU/yu8bk/Wyu/NV1u+20x9B3+O0LtxR5QiA7VoXISA==$0iAe9pL2kWDcEhJm72y0HB6qBlKAGQLq8H2ACX+NBRF2MrIjhQnOqTRjtdJYFm7WmjuLYFDQA3MRwtcy823RfHSoUJWm1HXxu2qO4esoixVnaFTckpObADd4eHiRQmX1cwEG7xLtq6YxgTdaPDlxsnghiL7WyR60pns5EwbNAf+ZfSrecB4ZLhhUfqQem3mY6nqBtC65/+vuzul6MlFxWkc7PZQvzb2tuJlVbF9+/EqP4uZJl5FfdKjzsvx7ZN86sd4MPXAI/JLlCBdJF1EJ2grBPcj8ExHxnjFZiaL5z1X+V8DTCKHCR62MH7XPUqzA1QvYrPWxvE0sWdfnIbN+T6uocmSwjTDco77Bill+u7HCcYGNLQWRYLcMo1TiBqZ/hf4XFbgm7CrBQbyhGgTiaIEb76MZmjoy5HKVUNb4c3T/krIriVcZarBu44Df2tTUU17Hcq67cP+xjhsy7+GcSL29bf8chFyLzcxLD0wVx8R8kgf1kOzY5Q==",
            "encryptedSecurityCode": "adyenjs_0_1_25$NUEoDTg8lgfVVOzHTd6U3wI0EF6uo8XgiK5c8NMHa6WIEq8Rdq4Tz7kNWfGZXLTQtWklRcOngywNtFuvZLA0V3GvZ75wepP7GhxhohzeXsRsUYs3vefcH1MAYoEbNB3l98MqcsXT6afg0dvTd91RCFXmAVyTuwgMdtaCvvSfaWWcjSlkjgOHPi/edZgMRhE49sB7Xamm6UOXBkscqspYh1osg5TN9Pg3B+4SQfdUFKS1dqc0LTFulQqycdLQ2WCH3C1Q5J2xecxQE4LW1lD6PmlgX8nEh6e617Reh+dgBp3Lu0OGkdpxyQYmcU+mrRizitTGHpJX3LI5F3C+3D54oA==$MiqdO9d4uuqXjdZY6bTReNmPPkeqJZin+y+kaWaTzcmQTmPOTOTu/wOHGX+EXGutXU8CMnOER7zSCPcMsXKgkyWqdOn9Np7su0GEd+i62MqSOzD0o2u5o1XrvlH+sx6cQ6v/kDYpTA4BKKoAiUgxPsYLthCSowigPNryc6T2tWjtlkMUNT1qcJCMeCDeoksMKAleI0pSXol4AAYqHEZMrvUJU9J1/+JeHBbVcT2/ZCClUwmCaOYOpTh02YP77V4efFzkf6jOCTp3fD1NSgmxu26ds0AnobgugQd7ljFgf97ZlAN3Lm3vWlZX1Oob0WC/DtnMmqbiR1rjjDt5Kh/pvDRTxlsu/piyIWY3Qqo94m9hSSdWS8PU/g5bcw55AfXwVnhOwkXF1+ABz8OYZK8+ZWAxS3HdvnKrBsz54HeYsIhY402bHF1lQoeh9ZUtKNaurLgiCf2XHq0rkgjg2j8C8h7wmSulMdhE0vLps2IklS+hHn/zYbuLVhsVPpcH23Hxty1go74z6Xh9Hl9RUy3BU6Sg3mNBy6liQDgQO/q6fTYYo4HXJQ+Zez6Y/cLGESJnqcF8JOD8o3PyKTUQLzdVtFtUTwR134eoa8+4bHkKOOVwPm0ND9pSNYXeNk6G5IAiZ3Kjt2BI6ZE/07LwMPCCz+wUc6R6a6pmryroq12JvrQDDVNysPMqJVwtveETJrd1nHkqXbY=",
            "holderName": "",
            "type": "scheme"
        }

        browser_info = {
            "userAgent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "language": "en-US",
            "colorDepth": 24,
            "screenHeight": 723,
            "screenWidth": 1536,
            "timeZoneOffset": 0,
            "javaEnabled": False
        }

        # Create Payment
        payment = AdyenController().adyen_payments(
            acquirer_id=payment_acquire_id,
            reference=transaction['reference'],
            converted_amount=transaction['converted_amount'],
            currency_id=transaction['currency_id'],
            partner_id=transaction['partner_id'],
            payment_method=payment_method,
            access_token=transaction['access_token'],
            browser_info=browser_info
        )
        print(payment)

        # Finalize Transaction
        test = PaymentPostProcessing().poll_status()
        print(test)

        # Validate Payment
        WebsiteSale().shop_payment_validate()

        # Confirm SO
        WebsiteSale().shop_payment_confirmation()

        return 'test'


class PaymentMutation(graphene.ObjectType):
    select_payment_acquirer = SelectPaymentAcquirer.Field(description='Select the Payment Acquirer')
    make_payment = MakePayment.Field(description='Creates a new payment request.')
