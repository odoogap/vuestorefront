# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import (
    Lead as VSFLead,
    State as VSFState,
    Country as VSFCountry,
    Company as VSFCompany,
    Pricelist as VSFPricelist,
    Partner as VSFPartner,
    User as VSFUser,
    Currency as VSFCurrency,
    Category as VSFCategory,
    AttributeValue as VSFAttributeValue,
    Attribute as VSFAttribute,
    ProductImage as VSFProductImage,
    Ribbon as VSFRibbon,
    Product as VSFProduct,
    Payment as VSFPayment,
    PaymentTransaction as VSFPaymentTransaction,
    OrderLine as VSFOrderLine,
    Coupon as VSFCoupon,
    GiftCard as VSFGiftCard,
    ShippingMethod as VSFShippingMethod,
    Order as VSFOrder,
    InvoiceLine as VSFInvoiceLine,
    Invoice as VSFInvoice,
    WishlistItem as VSFWishlistItem,
    PaymentIcon as VSFPaymentIcon,
    PaymentProvider as VSFPaymentProvider,
    MailingList as VSFMailingList,
    MailingContactSubscription as VSFMailingContactSubscription,
    MailingContact as VSFMailingContact,
    Website as VSFWebsite,
    WebsiteMenu as VSFWebsiteMenu,
    WebsiteMenuImage as VSFWebsiteMenuImage,
)


# --------------------- #
#       ENUMS           #
# --------------------- #


# --------------------- #
#      Functions        #
# --------------------- #


# --------------------- #
#       Objects         #
# --------------------- #

class CustomLead(VSFLead):
    id = graphene.Int(required=True)


class CustomState(VSFState):
    id = graphene.Int(required=True)


class CustomCountry(VSFCountry):
    id = graphene.Int(required=True)
    states = graphene.List(graphene.NonNull(lambda: CustomState))

    def resolve_states(self, info):
        return self.state_ids or None


class CustomCompany(VSFCompany):
    id = graphene.Int(required=True)
    country = graphene.Field(lambda: CustomCountry)
    state = graphene.Field(lambda: CustomState)

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_state(self, info):
        return self.state_id or None


class CustomPricelist(VSFPricelist):
    id = graphene.Int()
    currency = graphene.Field(lambda: CustomCurrency)

    def resolve_currency(self, info):
        return self.currency_id or None


class CustomPartner(VSFPartner):
    id = graphene.Int(required=True)
    country = graphene.Field(lambda: CustomCountry)
    state = graphene.Field(lambda: CustomState)
    billing_address = graphene.Field(lambda: CustomPartner)
    company = graphene.Field(lambda: CustomPartner)
    contacts = graphene.List(graphene.NonNull(lambda: CustomPartner))
    parent_id = graphene.Field(lambda: CustomPartner)
    public_pricelist = graphene.Field(lambda: CustomPricelist)
    current_pricelist = graphene.Field(lambda: CustomPricelist)

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_state(self, info):
        return self.state_id or None

    def resolve_billing_address(self, info):
        billing_address = self.child_ids.filtered(lambda a: a.type and a.type == 'invoice')
        return billing_address and billing_address[0] or None

    def resolve_company(self, info):
        return self.company_id.partner_id or None

    def resolve_contacts(self, info):
        return self.child_ids or None

    def resolve_parent_id(self, info):
        return self.parent_id or None

    def resolve_public_pricelist(self, info):
        website = self.env['website'].get_current_website()
        partner = website.user_id.sudo().partner_id
        return partner.last_website_so_id.pricelist_id or partner.property_product_pricelist

    def resolve_current_pricelist(self, info):
        website = self.env['website'].get_current_website()
        return website.get_current_pricelist()


class CustomUser(VSFUser):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: CustomPartner)

    def resolve_partner(self, info):
        return self.partner_id or None


class CustomCurrency(VSFCurrency):
    id = graphene.Int(required=True)


class CustomCategory(VSFCategory):
    id = graphene.Int(required=True)
    parent = graphene.Field(lambda: CustomCategory)
    childs = graphene.List(graphene.NonNull(lambda: CustomCategory))
    products = graphene.List(graphene.NonNull(lambda: CustomProduct))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_products(self, info):
        return self.product_tmpl_ids or None


class CustomAttributeValue(VSFAttributeValue):
    id = graphene.Int(required=True)
    attribute = graphene.Field(lambda: CustomAttribute)

    def resolve_attribute(self, info):
        return self.attribute_id or None


class CustomAttribute(VSFAttribute):
    id = graphene.Int(required=True)
    values = graphene.List(graphene.NonNull(lambda: CustomAttributeValue))

    def resolve_values(self, info):
        return self.value_ids or None


class CustomProductImage(VSFProductImage):
    id = graphene.Int(required=True)


class CustomRibbon(VSFRibbon):
    id = graphene.Int(required=True)


class CustomProduct(VSFProduct):
    id = graphene.Int(required=True)
    currency = graphene.Field(lambda: CustomCurrency)
    categories = graphene.List(graphene.NonNull(lambda: CustomCategory))
    media_gallery = graphene.List(graphene.NonNull(lambda: CustomProductImage))
    alternative_products = graphene.List(graphene.NonNull(lambda: CustomProduct))
    accessory_products = graphene.List(graphene.NonNull(lambda: CustomProduct))
    variant_attribute_values = graphene.List(graphene.NonNull(lambda: CustomAttributeValue),
                                             description='Specific to Product Variant')
    product_template = graphene.Field((lambda: CustomProduct), description='Specific to Product Variant')
    attribute_values = graphene.List(graphene.NonNull(lambda: CustomAttributeValue),
                                     description='Specific to Product Template')
    product_variants = graphene.List(graphene.NonNull(lambda: CustomProduct),
                                     description='Specific to Product Template')
    first_variant = graphene.Field((lambda: CustomProduct), description='Specific to use in Product Template')

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_categories(self, info):
        website = self.env['website'].get_current_website()
        if website:
            return self.public_categ_ids.filtered(
                lambda c: not c.website_id or c.website_id and c.website_id.id == website.id) or None
        return self.public_categ_ids or None

    def resolve_media_gallery(self, info):
        if self._name == 'product.template':
            return self.product_template_image_ids or None
        else:
            return self.product_template_image_ids + self.product_variant_image_ids or None

    def resolve_alternative_products(self, info):
        return self.alternative_product_ids or None

    def resolve_accessory_products(self, info):
        return self.accessory_product_ids or None

    def resolve_variant_attribute_values(self, info):
        return self.product_template_attribute_value_ids or None

    def resolve_product_template(self, info):
        return self.product_tmpl_id or None

    def resolve_attribute_values(self, info):
        return self.attribute_line_ids.product_template_value_ids or None

    def resolve_product_variants(self, info):
        return self.product_variant_ids or None

    def resolve_first_variant(self, info):
        return self.product_variant_id or None


class CustomPayment(VSFPayment):
    id = graphene.Int()


class CustomPaymentTransaction(VSFPaymentTransaction):
    id = graphene.Int()
    payment = graphene.Field(lambda: CustomPayment)
    currency = graphene.Field(lambda: CustomCurrency)
    company = graphene.Field(lambda: CustomPartner)
    customer = graphene.Field(lambda: CustomPartner)

    def resolve_payment(self, info):
        return self.payment_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_company(self, info):
        return self.company_id or None

    def resolve_customer(self, info):
        return self.partner_id or None


class CustomOrderLine(VSFOrderLine):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: CustomProduct)
    gift_card = graphene.Field(lambda: CustomGiftCard)
    coupon = graphene.Field(lambda: CustomCoupon)

    def resolve_product(self, info):
        return self.product_id or None

    def resolve_gift_card(self, info):
        gift_card = None
        if self.coupon_id and self.coupon_id.program_type and self.coupon_id.program_type == 'gift_card':
            gift_card = self.coupon_id
        return gift_card

    def resolve_coupon(self, info):
        coupon = None
        if self.coupon_id and self.coupon_id.program_type and self.coupon_id.program_type == 'coupons':
            coupon = self.coupon_id
        return coupon


class CustomCoupon(VSFCoupon):
    id = graphene.Int(required=True)


class CustomGiftCard(VSFGiftCard):
    id = graphene.Int(required=True)


class CustomShippingMethod(VSFShippingMethod):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: CustomProduct)

    def resolve_product(self, info):
        return self.product_id or None


class CustomOrder(VSFOrder):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: CustomPartner)
    partner_shipping = graphene.Field(lambda: CustomPartner)
    partner_invoice = graphene.Field(lambda: CustomPartner)
    shipping_method = graphene.Field(lambda: CustomShippingMethod)
    currency = graphene.Field(lambda: CustomCurrency)
    order_lines = graphene.List(graphene.NonNull(lambda: CustomOrderLine))
    website_order_line = graphene.List(graphene.NonNull(lambda: CustomOrderLine))
    transactions = graphene.List(graphene.NonNull(lambda: CustomPaymentTransaction))
    last_transaction = graphene.Field(lambda: CustomPaymentTransaction)
    coupons = graphene.List(graphene.NonNull(lambda: CustomCoupon))
    gift_cards = graphene.List(graphene.NonNull(lambda: CustomGiftCard))

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_partner_invoice(self, info):
        return self.partner_invoice_id or None

    def resolve_shipping_method(self, info):
        return self.carrier_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_order_lines(self, info):
        return self.order_line or None

    def resolve_website_order_line(self, info):
        return self.website_order_line or None

    def resolve_transactions(self, info):
        return self.transaction_ids or None

    def resolve_last_transaction(self, info):
        if self.transaction_ids:
            return self.transaction_ids.sorted(key=lambda r: r.create_date, reverse=True)[0]
        return None

    def resolve_coupons(self, info):
        return self.applied_coupon_ids.filtered(lambda c: c.program_type == 'coupons') or None

    def resolve_gift_cards(self, info):
        return self.applied_coupon_ids.filtered(lambda c: c.program_type == 'gift_card') or None


class CustomInvoiceLine(VSFInvoiceLine):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: CustomProduct)

    def resolve_product(self, info):
        return self.product_id or None


class CustomInvoice(VSFInvoice):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: CustomPartner)
    partner_shipping = graphene.Field(lambda: CustomPartner)
    currency = graphene.Field(lambda: CustomCurrency)
    invoice_lines = graphene.List(graphene.NonNull(lambda: CustomInvoiceLine))
    transactions = graphene.List(graphene.NonNull(lambda: CustomPaymentTransaction))

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_invoice_lines(self, info):
        return self.invoice_line_ids or None

    def resolve_transactions(self, info):
        return self.transaction_ids or None


class CustomWishlistItem(VSFWishlistItem):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: CustomPartner)
    product = graphene.Field(lambda: CustomProduct)

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_product(self, info):
        return self.product_id or None


class CustomPaymentIcon(VSFPaymentIcon):
    id = graphene.Int()


class CustomPaymentProvider(VSFPaymentProvider):
    id = graphene.Int(required=True)
    payment_icons = graphene.List(graphene.NonNull(lambda: CustomPaymentIcon))

    def resolve_payment_icons(self, info):
        return self.payment_icon_ids or None


class CustomMailingList(VSFMailingList):
    id = graphene.Int(required=True)


class CustomMailingContactSubscription(VSFMailingContactSubscription):
    id = graphene.Int(required=True)
    mailing_list = graphene.Field(lambda: CustomMailingList)

    def resolve_mailing_list(self, info):
        return self.list_id or None


class CustomMailingContact(VSFMailingContact):
    id = graphene.Int()
    subscription_list = graphene.List(graphene.NonNull(lambda: VSFMailingContactSubscription))

    def resolve_subscription_list(self, info):
        return self.subscription_list_ids or None


class CustomWebsite(VSFWebsite):
    id = graphene.Int()
    company = graphene.Field(lambda: CustomCompany)
    public_user = graphene.Field(lambda: CustomUser)

    def resolve_company(self, info):
        return self.company_id or None

    def resolve_public_user(self, info):
        return self.user_id or None


class CustomWebsiteMenu(VSFWebsiteMenu):
    id = graphene.Int(required=True)
    parent = graphene.Field(lambda: CustomWebsiteMenu)
    childs = graphene.List(graphene.NonNull(lambda: CustomWebsiteMenu))
    images = graphene.List(graphene.NonNull(lambda: CustomWebsiteMenuImage))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_images(self, info):
        return self.menu_image_ids or None


class CustomWebsiteMenuImage(VSFWebsiteMenuImage):
    id = graphene.Int(required=True)
