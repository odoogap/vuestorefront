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

class ClaLead(VSFLead):
    id = graphene.Int(required=True)


class ClaState(VSFState):
    id = graphene.Int(required=True)


class ClaCountry(VSFCountry):
    id = graphene.Int(required=True)
    states = graphene.List(graphene.NonNull(lambda: ClaState))

    def resolve_states(self, info):
        return self.state_ids or None


class ClaCompany(VSFCompany):
    id = graphene.Int(required=True)
    country = graphene.Field(lambda: ClaCountry)
    state = graphene.Field(lambda: ClaState)

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_state(self, info):
        return self.state_id or None


class ClaPricelist(VSFPricelist):
    id = graphene.Int()
    currency = graphene.Field(lambda: ClaCurrency)

    def resolve_currency(self, info):
        return self.currency_id or None


class ClaPartner(VSFPartner):
    id = graphene.Int(required=True)
    country = graphene.Field(lambda: ClaCountry)
    state = graphene.Field(lambda: ClaState)
    billing_address = graphene.Field(lambda: ClaPartner)
    company = graphene.Field(lambda: ClaPartner)
    contacts = graphene.List(graphene.NonNull(lambda: ClaPartner))
    parent_id = graphene.Field(lambda: ClaPartner)
    public_pricelist = graphene.Field(lambda: ClaPricelist)
    current_pricelist = graphene.Field(lambda: ClaPricelist)

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


class ClaUser(VSFUser):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: ClaPartner)

    def resolve_partner(self, info):
        return self.partner_id or None


class ClaCurrency(VSFCurrency):
    id = graphene.Int(required=True)


class ClaCategory(VSFCategory):
    id = graphene.Int(required=True)
    parent = graphene.Field(lambda: ClaCategory)
    childs = graphene.List(graphene.NonNull(lambda: ClaCategory))
    products = graphene.List(graphene.NonNull(lambda: ClaProduct))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_products(self, info):
        return self.product_tmpl_ids or None


class ClaAttributeValue(VSFAttributeValue):
    id = graphene.Int(required=True)
    attribute = graphene.Field(lambda: ClaAttribute)

    def resolve_attribute(self, info):
        return self.attribute_id or None


class ClaAttribute(VSFAttribute):
    id = graphene.Int(required=True)
    values = graphene.List(graphene.NonNull(lambda: ClaAttributeValue))

    def resolve_values(self, info):
        return self.value_ids or None


class ClaProductImage(VSFProductImage):
    id = graphene.Int(required=True)


class ClaRibbon(VSFRibbon):
    id = graphene.Int(required=True)


class ClaProduct(VSFProduct):
    id = graphene.Int(required=True)
    currency = graphene.Field(lambda: ClaCurrency)
    categories = graphene.List(graphene.NonNull(lambda: ClaCategory))
    media_gallery = graphene.List(graphene.NonNull(lambda: ClaProductImage))
    alternative_products = graphene.List(graphene.NonNull(lambda: ClaProduct))
    accessory_products = graphene.List(graphene.NonNull(lambda: ClaProduct))
    variant_attribute_values = graphene.List(graphene.NonNull(lambda: ClaAttributeValue),
                                             description='Specific to Product Variant')
    product_template = graphene.Field((lambda: ClaProduct), description='Specific to Product Variant')
    attribute_values = graphene.List(graphene.NonNull(lambda: ClaAttributeValue),
                                     description='Specific to Product Template')
    product_variants = graphene.List(graphene.NonNull(lambda: ClaProduct),
                                     description='Specific to Product Template')
    first_variant = graphene.Field((lambda: ClaProduct), description='Specific to use in Product Template')

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


class ClaPayment(VSFPayment):
    id = graphene.Int()


class ClaPaymentTransaction(VSFPaymentTransaction):
    id = graphene.Int()
    payment = graphene.Field(lambda: ClaPayment)
    currency = graphene.Field(lambda: ClaCurrency)
    company = graphene.Field(lambda: ClaPartner)
    customer = graphene.Field(lambda: ClaPartner)

    def resolve_payment(self, info):
        return self.payment_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_company(self, info):
        return self.company_id or None

    def resolve_customer(self, info):
        return self.partner_id or None


class ClaOrderLine(VSFOrderLine):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: ClaProduct)
    gift_card = graphene.Field(lambda: ClaGiftCard)
    coupon = graphene.Field(lambda: ClaCoupon)

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


class ClaCoupon(VSFCoupon):
    id = graphene.Int(required=True)


class ClaGiftCard(VSFGiftCard):
    id = graphene.Int(required=True)


class ClaShippingMethod(VSFShippingMethod):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: ClaProduct)

    def resolve_product(self, info):
        return self.product_id or None


class ClaOrder(VSFOrder):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: ClaPartner)
    partner_shipping = graphene.Field(lambda: ClaPartner)
    partner_invoice = graphene.Field(lambda: ClaPartner)
    shipping_method = graphene.Field(lambda: ClaShippingMethod)
    currency = graphene.Field(lambda: ClaCurrency)
    order_lines = graphene.List(graphene.NonNull(lambda: ClaOrderLine))
    website_order_line = graphene.List(graphene.NonNull(lambda: ClaOrderLine))
    transactions = graphene.List(graphene.NonNull(lambda: ClaPaymentTransaction))
    last_transaction = graphene.Field(lambda: ClaPaymentTransaction)
    coupons = graphene.List(graphene.NonNull(lambda: ClaCoupon))
    gift_cards = graphene.List(graphene.NonNull(lambda: ClaGiftCard))

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


class ClaInvoiceLine(VSFInvoiceLine):
    id = graphene.Int(required=True)
    product = graphene.Field(lambda: ClaProduct)

    def resolve_product(self, info):
        return self.product_id or None


class ClaInvoice(VSFInvoice):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: ClaPartner)
    partner_shipping = graphene.Field(lambda: ClaPartner)
    currency = graphene.Field(lambda: ClaCurrency)
    invoice_lines = graphene.List(graphene.NonNull(lambda: ClaInvoiceLine))
    transactions = graphene.List(graphene.NonNull(lambda: ClaPaymentTransaction))

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


class ClaWishlistItem(VSFWishlistItem):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: ClaPartner)
    product = graphene.Field(lambda: ClaProduct)

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_product(self, info):
        return self.product_id or None


class ClaPaymentIcon(VSFPaymentIcon):
    id = graphene.Int()


class ClaPaymentProvider(VSFPaymentProvider):
    id = graphene.Int(required=True)
    payment_icons = graphene.List(graphene.NonNull(lambda: ClaPaymentIcon))

    def resolve_payment_icons(self, info):
        return self.payment_icon_ids or None


class ClaMailingList(VSFMailingList):
    id = graphene.Int(required=True)


class ClaMailingContactSubscription(VSFMailingContactSubscription):
    id = graphene.Int(required=True)
    mailing_list = graphene.Field(lambda: ClaMailingList)

    def resolve_mailing_list(self, info):
        return self.list_id or None


class ClaMailingContact(VSFMailingContact):
    id = graphene.Int()
    subscription_list = graphene.List(graphene.NonNull(lambda: VSFMailingContactSubscription))

    def resolve_subscription_list(self, info):
        return self.subscription_list_ids or None


class ClaWebsite(VSFWebsite):
    id = graphene.Int()
    company = graphene.Field(lambda: ClaCompany)
    public_user = graphene.Field(lambda: ClaUser)

    def resolve_company(self, info):
        return self.company_id or None

    def resolve_public_user(self, info):
        return self.user_id or None


class ClaWebsiteMenu(VSFWebsiteMenu):
    id = graphene.Int(required=True)
    parent = graphene.Field(lambda: ClaWebsiteMenu)
    childs = graphene.List(graphene.NonNull(lambda: ClaWebsiteMenu))
    images = graphene.List(graphene.NonNull(lambda: ClaWebsiteMenuImage))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_images(self, info):
        return self.menu_image_ids or None


class ClaWebsiteMenuImage(VSFWebsiteMenuImage):
    id = graphene.Int(required=True)
