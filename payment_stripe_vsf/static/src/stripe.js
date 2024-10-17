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
        this.stripeJs = Stripe('pk_test_51Q5TQCCsRfUCvfWIlYOylZI5rSJ0FoqZGBFSFQ9rdDGmr6ZXTjKk038fWG7YPCDHzVlQsP5fAPp7Frxs2bFMVacC00CSEYMmw3', {
            'apiVersion': '2019-05-16',  // The API version of Stripe implemented in this module.
        });
        let clientSecret = 'pi_3QAxLoCsRfUCvfWI1BsCKtp1_secret_ik0R8Ez0lvJJcQq1wpl93cCyt';
        this.clientSecret = clientSecret;
        this.billingDetails = {
            "name": "Test02",
            "email": "test02@hotmail.com",
            "phone": "966222333",
            "address": {
                "line1": "Rua Nossa Senhora de Fatima",
                "line2": "",
                "city": "Viseu",
                "state": "18",
                "country": "PT",
                "postal_code": "3510-605"
            }
        }
        this.return_url = `http://2f2e-2001-818-de5d-da00-3f59-eac8-191a-c707.ngrok-free.app/payment/stripe/return?reference=S00070-1`;
        let elementsOptions =  {
            appearance: { theme: 'stripe' },
            currency: "usd",
            captureMethod: "automatic",
            mode: 'payment',
            amount:7381,
            paymentMethodTypes: ['card', 'klarna', 'paypal']
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
        } else if (this.paymentType === 'paypal') {
            return this.stripeJs.confirmPayPalPayment(this.clientSecret,
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
