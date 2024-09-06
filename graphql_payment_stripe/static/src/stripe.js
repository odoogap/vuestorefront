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
        this.stripeJs = Stripe('pk_test_owCYEBbtz5mwrtoCMDNQXB6W', {
            'apiVersion': '2019-05-16',  // The API version of Stripe implemented in this module.
        });
        let clientSecret = 'pi_3PvywMEx8HtT00q81iWquJ3H_secret_tGH9LDmMRyUzsV9shZvcioX9y';
        this.clientSecret = clientSecret;
        this.billingDetails = {
            "name": "Mitchell Admin",
            "email": "admin@yourcompany.example.com",
            "phone": "+1 555-555-5555",
            "address": {
                "line1": "215 Vine St",
                "line2": "",
                "city": "Scranton",
                "state": "PA",
                "country": "US",
                "postal_code": "18503"
            },
        }
        this.return_url = `http://7f9e-2405-201-202b-815-35f3-8cff-6ce1-8bd5.ngrok-free.app/payment/stripe/return?reference=S00044`;
        let elementsOptions =  {
            appearance: { theme: 'stripe' },
            captureMethod: "automatic",
            mode: 'payment',
            amount:1900,
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