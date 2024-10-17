/** @odoo-module **/
/* global Stripe */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSaleStripe = publicWidget.Widget.extend({
    selector: '#stripe_checkout',
    events: {
        'submit form#payment-form': '_onClickCheckoutSubmit',
    },
    init: function () {
        let self = this;
        this._super.apply(this, arguments);
        this.stripeJs = Stripe('pk_test_51Q5ULNFMmqSmtPHODi8Nwo25z2hnU5TJ2r76oWuYeJwVSrjNlThcieFc5Nmt46cw1kLrcRMDizyzgZE7vUOVlMih00y4iZJn5U', {
            'apiVersion': '2019-05-16',  // The API version of Stripe implemented in this module.
        });
        let clientSecret = 'pi_3QAwbeFMmqSmtPHO0HP0pDxO_secret_mKWy2T2iZoWfp0aX5Z6w4ezCo';
        this.clientSecret = clientSecret;
        this.billingDetails = {
            "name": "Test02 Affirm",
            "email": "test02a@hotmail.com",
            "phone": "8436726176",
            "address": {
                "line1": "1883 Broadway Street",
                "line2": "",
                "city": "Pageland",
                "state": "NC",
                "country": "US",
                "postal_code": "29728"
            }
        }
        this.return_url = `http://2f2e-2001-818-de5d-da00-3f59-eac8-191a-c707.ngrok-free.app/payment/stripe/return?reference=S00093`;
        let elementsOptions =  {
            appearance: { theme: 'stripe' },
            currency: "usd",
            captureMethod: "automatic",
            mode: 'payment',
            amount:37000,
            paymentMethodTypes: ['card', 'affirm', 'klarna']
        };
        this.paymentType = '';
        const paymentElementOptions = {
            defaultValues: {
                billingDetails: this.billingDetails
            }
        };
        this.elements = this.stripeJs.elements({ clientSecret , elementsOptions });
        const paymentElement = this.elements.create('payment', paymentElementOptions);
        paymentElement.mount('#payment-element');
        paymentElement.on('change', function(event) {
            if (event.complete) {
                self.paymentType = event.value.type;
            }
        })
    },
    async _onClickCheckoutSubmit(event) {
        event.preventDefault();
        const self = this;
        let elements = this.elements;
        if (this.paymentType === 'affirm') {
            return this.stripeJs.confirmAffirmPayment(this.clientSecret,
                {
                    payment_method: {
                    billing_details: self.billingDetails
                },
                // Return URL where the customer should be redirected after the authorization.
                return_url: self.return_url
            });
        } else if (this.paymentType === 'klarna') {
            return this.stripeJs.confirmKlarnaPayment(this.clientSecret,
                {
                    payment_method: {
                    billing_details: self.billingDetails
                },
                // Return URL where the customer should be redirected after the authorization.
                return_url: self.return_url
            });
        } else {
            return this.stripeJs.confirmPayment({
                elements,
                confirmParams: {
                    return_url: self.return_url
                },
            });
        }

        // if (error) {
        //     console.error(error);
        //     alert(error);
        // } else if (paymentIntent && paymentIntent.status === "succeeded") {
        //     console.log("Payment succeeded");
        //     alert(paymentIntent);
        // } else {
        //     console.log("Payment failed");
        //     alert("Payment failed");
        // }
    },
})
