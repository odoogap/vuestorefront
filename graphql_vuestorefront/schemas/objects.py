# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import SUPERUSER_ID, _

from odoo.addons.http_routing.models.ir_http import slugify
from odoo.addons.graphql_base import OdooObjectType
from odoo.exceptions import AccessError
from odoo.http import request


# --------------------- #
#       ENUMS           #
# --------------------- #

AddressType = graphene.Enum('AddressType', [('Contact', 'contact'), ('InvoiceAddress', 'invoice'),
                                            ('DeliveryAddress', 'delivery'), ('OtherAddress', 'other'),
                                            ('PrivateAddress', 'private')])

VariantCreateMode = graphene.Enum('VariantCreateMode', [('Instantly', 'always'), ('Dynamically', 'dynamically'),
                                                        ('NeverOption', 'no_variant')])

FilterVisibility = graphene.Enum('FilterVisibility', [('Visible', 'visible'), ('Hidden', 'hidden')])

OrderStage = graphene.Enum('OrderStage', [('Quotation', 'draft'), ('QuotationSent', 'sent'),
                                          ('SalesOrder', 'sale'), ('Locked', 'done'), ('Cancelled', 'cancel')])

InvoiceStatus = graphene.Enum('InvoiceStatus', [('UpsellingOpportunity', 'upselling'), ('FullyInvoiced', 'invoiced'),
                                                ('ToInvoice', 'to invoice'), ('NothingtoInvoice', 'no')])

InvoiceState = graphene.Enum('InvoiceState', [('Draft', 'draft'), ('Posted', 'posted'), ('Cancelled', 'cancel')])

PaymentTransactionState = graphene.Enum('PaymentTransactionState', [('Draft', 'draft'), ('Pending', 'pending'),
                                                               ('Authorized', 'authorized'), ('Confirmed', 'done'),
                                                               ('Canceled', 'cancel'), ('Error', 'error')])


class SortEnum(graphene.Enum):
    ASC = 'ASC'
    DESC = 'DESC'


# --------------------- #
#      Functions        #
# --------------------- #

def get_document_with_check_access(model, domain, order=None, limit=20, offset=0,
                                   error_msg='This document does not exist.'):
    document = model.search(domain, order=order, limit=limit, offset=offset)
    document_sudo = document.with_user(SUPERUSER_ID).exists()
    if document and not document_sudo:
        raise GraphQLError(_(error_msg))
    try:
        document.check_access_rights('read')
        document.check_access_rule('read')
    except AccessError:
        return []
    return document_sudo


def get_document_count_with_check_access(model, domain):
    try:
        model.check_access_rights('read')
        model.check_access_rule('read')
    except AccessError:
        return 0
    return model.search_count(domain)


def get_product_pricing_info(env, product):
    website = env['website'].get_current_website()
    pricelist = website.get_current_pricelist()
    return product and product._get_combination_info_variant(pricelist=pricelist) or None


def product_is_in_wishlist(env, product):
    website = env['website'].get_current_website()
    request.website = website
    return product._is_in_wishlist()


# --------------------- #
#       Objects         #
# --------------------- #

class Lead(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()
    company = graphene.String()
    subject = graphene.String()
    message = graphene.String()

    def resolve_name(self, info):
        return self.contact_name

    def resolve_email(self, info):
        return self.email_from

    def resolve_company(self, info):
        return self.partner_name

    def resolve_subject(self, info):
        return self.name

    def resolve_message(self, info):
        return self.description


class State(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)
    code = graphene.String(required=True)


class Country(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)
    code = graphene.String(required=True)
    states = graphene.List(graphene.NonNull(lambda: State))
    image_url = graphene.String()

    def resolve_states(self, info):
        return self.state_ids or None


class Company(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    street = graphene.String()
    street2 = graphene.String()
    city = graphene.String()
    country = graphene.Field(lambda: Country)
    state = graphene.Field(lambda: State)
    zip = graphene.String()
    email = graphene.String()
    phone = graphene.String()
    mobile = graphene.String()
    image = graphene.String()
    vat = graphene.String()
    social_twitter = graphene.String()
    social_facebook = graphene.String()
    social_github = graphene.String()
    social_linkedin = graphene.String()
    social_youtube = graphene.String()
    social_instagram = graphene.String()

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_state(self, info):
        return self.state_id or None

    def resolve_image(self, info):
        return '/web/image/res.company/{}/image_1920'.format(self.id)


class Pricelist(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    currency = graphene.Field(lambda: Currency)

    def resolve_currency(self, info):
        return self.currency_id or None


class Partner(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    street = graphene.String()
    street2 = graphene.String()
    city = graphene.String()
    country = graphene.Field(lambda: Country)
    state = graphene.Field(lambda: State)
    zip = graphene.String()
    email = graphene.String()
    phone = graphene.String()
    mobile = graphene.String()
    address_type = AddressType()
    billing_address = graphene.Field(lambda: Partner)
    is_company = graphene.Boolean(required=True)
    company = graphene.Field(lambda: Partner)
    contacts = graphene.List(graphene.NonNull(lambda: Partner))
    signup_token = graphene.String()
    signup_valid = graphene.String()
    parent_id = graphene.Field(lambda: Partner)
    image = graphene.String()
    vat = graphene.String()
    public_pricelist = graphene.Field(lambda: Pricelist)
    current_pricelist = graphene.Field(lambda: Pricelist)

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_state(self, info):
        return self.state_id or None

    def resolve_address_type(self, info):
        return self.type or None

    def resolve_billing_address(self, info):
        billing_address = self.child_ids.filtered(lambda a: a.type and a.type == 'invoice')
        return billing_address and billing_address[0] or None

    def resolve_company(self, info):
        return self.company_id.partner_id or None

    def resolve_contacts(self, info):
        return self.child_ids or None

    def resolve_parent_id(self, info):
        return self.parent_id or None

    def resolve_image(self, info):
        return '/web/image/res.partner/{}/image_1920'.format(self.id)

    def resolve_public_pricelist(self, info):
        website = self.env['website'].get_current_website()
        partner = website.user_id.sudo().partner_id
        return partner.last_website_so_id.pricelist_id or partner.property_product_pricelist

    def resolve_current_pricelist(self, info):
        website = self.env['website'].get_current_website()
        return website.get_current_pricelist()


class User(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    partner = graphene.Field(lambda: Partner)

    def resolve_email(self, info):
        return self.login or None

    def resolve_partner(self, info):
        return self.partner_id or None


class Currency(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    symbol = graphene.String()


class Category(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    parent = graphene.Field(lambda: Category)
    childs = graphene.List(graphene.NonNull(lambda: Category))
    slug = graphene.String()
    products = graphene.List(graphene.NonNull(lambda: Product))
    json_ld = generic.GenericScalar()

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_slug(self, info):
        return self.website_slug

    def resolve_products(self, info):
        return self.product_tmpl_ids or None

    def resolve_json_ld(self, info):
        return self and self.get_json_ld() or None


class AttributeValue(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    display_type = graphene.String()
    html_color = graphene.String()
    search = graphene.String()
    price_extra = graphene.Float(description='Not use in the return Attributes List of the Products Query')
    attribute = graphene.Field(lambda: Attribute)

    def resolve_id(self, info):
        return self.id or None

    def resolve_search(self, info):
        attribute_id = self.attribute_id.id
        attribute_value_id = self.id
        return '{}-{}'.format(attribute_id, attribute_value_id) or None

    def resolve_attribute(self, info):
        return self.attribute_id or None


class Attribute(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    display_type = graphene.String()
    variant_create_mode = VariantCreateMode()
    filter_visibility = FilterVisibility()
    values = graphene.List(graphene.NonNull(lambda: AttributeValue))

    def resolve_variant_create_mode(self, info):
        return self.create_variant or None

    def resolve_filter_visibility(self, info):
        return self.visibility or None

    def resolve_values(self, info):
        return self.value_ids or None


class ProductImage(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    image = graphene.String()
    image_filename = graphene.String()
    video = graphene.String()

    def resolve_id(self, info):
        return self.id or None

    def resolve_image(self, info):
        return '/web/image/product.image/{}/image_1920'.format(self.id)

    def resolve_image_filename(self, info):
        return slugify(self.name)

    def resolve_video(self, info):
        return self.video_url or None


class Ribbon(OdooObjectType):
    id = graphene.Int(required=True)
    html = graphene.String()
    text_color = graphene.String()
    html_class = graphene.String()
    bg_color = graphene.String()
    display_name = graphene.String()


class Product(OdooObjectType):
    id = graphene.Int(required=True)
    type_id = graphene.String()
    visibility = graphene.Int()
    status = graphene.Int()
    name = graphene.String()
    display_name = graphene.String()
    sku = graphene.String()
    barcode = graphene.String()
    description = graphene.String()
    currency = graphene.Field(lambda: Currency)
    weight = graphene.Float()
    meta_title = graphene.String()
    meta_keyword = graphene.String()
    meta_description = graphene.String()
    image = graphene.String()
    small_image = graphene.String()
    image_filename = graphene.String()
    thumbnail = graphene.String()
    categories = graphene.List(graphene.NonNull(lambda: Category))
    allow_out_of_stock = graphene.Boolean()
    show_available_qty = graphene.Boolean()
    out_of_stock_message = graphene.String()
    ribbon = graphene.Field(lambda: Ribbon)
    is_in_stock = graphene.Boolean()
    is_in_wishlist = graphene.Boolean()
    media_gallery = graphene.List(graphene.NonNull(lambda: ProductImage))
    qty = graphene.Float()
    slug = graphene.String()
    alternative_products = graphene.List(graphene.NonNull(lambda: Product))
    accessory_products = graphene.List(graphene.NonNull(lambda: Product))
    # Specific to use in Product Variant
    combination_info_variant = generic.GenericScalar(description='Specific to Product Variant')
    variant_price = graphene.Float(description='Specific to Product Variant')
    variant_price_after_discount = graphene.Float(description='Specific to Product Variant')
    variant_has_discounted_price = graphene.Boolean(description='Specific to Product Variant')
    is_variant_possible = graphene.Boolean(description='Specific to Product Variant')
    variant_attribute_values = graphene.List(graphene.NonNull(lambda: AttributeValue),
                                             description='Specific to Product Variant')
    product_template = graphene.Field((lambda: Product), description='Specific to Product Variant')
    # Specific to use in Product Template
    combination_info = generic.GenericScalar(description='Specific to Product Template')
    price = graphene.Float(description='Specific to Product Template')
    attribute_values = graphene.List(graphene.NonNull(lambda: AttributeValue),
                                     description='Specific to Product Template')
    product_variants = graphene.List(graphene.NonNull(lambda: Product), description='Specific to Product Template')
    first_variant = graphene.Field((lambda: Product), description='Specific to use in Product Template')
    json_ld = generic.GenericScalar()

    def resolve_type_id(self, info):
        if self.detailed_type == 'product':
            return 'simple'
        else:
            return 'configurable'

    def resolve_visibility(self, info):
        if self.website_published:
            return 1
        else:
            return 0

    def resolve_status(self, info):
        if self.free_qty > 0:
            return 1
        else:
            return 0

    def resolve_sku(self, info):
        return self.default_code or None

    def resolve_description(self, info):
        return self.description_sale or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_meta_title(self, info):
        return self.website_meta_title or None

    def resolve_meta_keyword(self, info):
        return self.website_meta_keywords or None

    def resolve_meta_description(self, info):
        return self.website_meta_description or None

    def resolve_image(self, info):
        return '/web/image/{}/{}/image_1920'.format(self._name, self.id)

    def resolve_small_image(self, info):
        return '/web/image/{}/{}/image_128'.format(self._name, self.id)

    def resolve_image_filename(self, info):
        return slugify(self.name)

    def resolve_thumbnail(self, info):
        return '/web/image/{}/{}/image_512'.format(self._name, self.id)

    def resolve_categories(self, info):
        website = self.env['website'].get_current_website()
        if website:
            return self.public_categ_ids.filtered(
                lambda c: not c.website_id or c.website_id and c.website_id.id == website.id) or None
        return self.public_categ_ids or None

    def resolve_allow_out_of_stock(self, info):
        return self.allow_out_of_stock_order or None

    def resolve_show_available_qty(self, info):
        return self.show_availability or None

    def resolve_ribbon(self, info):
        return self.website_ribbon_id or None

    def resolve_is_in_stock(self, info):
        return bool(self.free_qty > 0)

    def resolve_is_in_wishlist(self, info):
        env = info.context["env"]
        is_in_wishlist = product_is_in_wishlist(env, self)
        return bool(is_in_wishlist)

    def resolve_media_gallery(self, info):
        if self._name == 'product.template':
            return self.product_template_image_ids or None
        else:
            return self.product_template_image_ids + self.product_variant_image_ids or None

    def resolve_qty(self, info):
        return self.free_qty

    def resolve_slug(self, info):
        return self.website_slug

    def resolve_alternative_products(self, info):
        return self.alternative_product_ids or None

    def resolve_accessory_products(self, info):
        return self.accessory_product_ids or None

    # Specific to use in Product Variant
    def resolve_combination_info_variant(self, info):
        env = info.context["env"]
        pricing_info = get_product_pricing_info(env, self)
        return pricing_info or None

    def resolve_variant_price(self, info):
        env = info.context["env"]
        pricing_info = get_product_pricing_info(env, self)
        return pricing_info['list_price'] or None

    def resolve_variant_price_after_discount(self, info):
        env = info.context["env"]
        pricing_info = get_product_pricing_info(env, self)
        return pricing_info['price'] or None

    def resolve_variant_has_discounted_price(self, info):
        env = info.context["env"]
        pricing_info = get_product_pricing_info(env, self)
        return pricing_info['has_discounted_price']

    def resolve_is_variant_possible(self, info):
        return self._is_variant_possible()

    def resolve_variant_attribute_values(self, info):
        return self.product_template_attribute_value_ids or None

    def resolve_product_template(self, info):
        return self.product_tmpl_id or None

    # Specific to use in Product Template
    def resolve_combination_info(self, info):
        env = info.context["env"]
        pricing_info = get_product_pricing_info(env, self.product_variant_id)
        return pricing_info or None

    def resolve_price(self, info):
        return self.list_price or None

    def resolve_attribute_values(self, info):
        return self.attribute_line_ids.product_template_value_ids or None

    def resolve_product_variants(self, info):
        return self.product_variant_ids or None

    def resolve_first_variant(self, info):
        return self.product_variant_id or None

    def resolve_json_ld(self, info):
        return self and self.get_json_ld() or None


class Payment(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    amount = graphene.Float()
    payment_reference = graphene.String()


class PaymentTransaction(OdooObjectType):
    id = graphene.Int()
    reference = graphene.String()
    payment = graphene.Field(lambda: Payment)
    amount = graphene.Float()
    currency = graphene.Field(lambda: Currency)
    provider = graphene.String()
    provider_reference = graphene.String()
    company = graphene.Field(lambda: Partner)
    customer = graphene.Field(lambda: Partner)
    state = PaymentTransactionState()

    def resolve_payment(self, info):
        return self.payment_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_provider(self, info):
        return self.provider_id.name or None

    def resolve_company(self, info):
        return self.company_id or None

    def resolve_customer(self, info):
        return self.partner_id or None


class OrderLine(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    product = graphene.Field(lambda: Product)
    quantity = graphene.Float()
    price_unit = graphene.Float()
    price_subtotal = graphene.Float()
    price_total = graphene.Float()
    price_tax = graphene.Float()
    shop_warning = graphene.String()
    gift_card = graphene.Field(lambda: GiftCard)
    coupon = graphene.Field(lambda: Coupon)

    def resolve_product(self, info):
        return self.product_id or None

    def resolve_quantity(self, info):
        return self.product_uom_qty or None

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


class Coupon(OdooObjectType):
    id = graphene.Int(required=True)
    code = graphene.String()


class GiftCard(OdooObjectType):
    id = graphene.Int(required=True)
    code = graphene.String()


class ShippingMethod(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    price = graphene.Float()
    product = graphene.Field(lambda: Product)

    def resolve_price(self, info):
        website = self.env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order(force_create=True)
        return self.rate_shipment(order)['price'] if self.free_over else self.fixed_price

    def resolve_product(self, info):
        return self.product_id or None


class Order(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    partner = graphene.Field(lambda: Partner)
    partner_shipping = graphene.Field(lambda: Partner)
    partner_invoice = graphene.Field(lambda: Partner)
    date_order = graphene.String()
    tax_totals = generic.GenericScalar()
    amount_untaxed = graphene.Float()
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    amount_delivery = graphene.Float()
    amount_subtotal = graphene.Float()
    amount_discounts = graphene.Float()
    amount_gift_cards = graphene.Float()
    currency_rate = graphene.String()
    shipping_method = graphene.Field(lambda: ShippingMethod)
    currency = graphene.Field(lambda: Currency)
    order_lines = graphene.List(graphene.NonNull(lambda: OrderLine))
    website_order_line = graphene.List(graphene.NonNull(lambda: OrderLine))
    stage = OrderStage()
    order_url = graphene.String()
    transactions = graphene.List(graphene.NonNull(lambda: PaymentTransaction))
    last_transaction = graphene.Field(lambda: PaymentTransaction)
    client_order_ref = graphene.String()
    invoice_status = InvoiceStatus()
    invoice_count = graphene.Int()
    coupons = graphene.List(graphene.NonNull(lambda: Coupon))
    gift_cards = graphene.List(graphene.NonNull(lambda: GiftCard))
    cart_quantity = graphene.Int()

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_partner_invoice(self, info):
        return self.partner_invoice_id or None

    def resolve_date_order(self, info):
        return self.date_order or None

    def resolve_tax_totals(self, info):
        return self.tax_totals or None

    def resolve_shipping_method(self, info):
        return self.carrier_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_order_lines(self, info):
        return self.order_line or None

    def resolve_website_order_line(self, info):
        return self.website_order_line or None

    def resolve_stage(self, info):
        return self.state or None

    def resolve_order_url(self, info):
        return self.get_portal_url() or None

    def resolve_transactions(self, info):
        return self.transaction_ids or None

    def resolve_last_transaction(self, info):
        if self.transaction_ids:
            return self.transaction_ids.sorted(key=lambda r: r.create_date, reverse=True)[0]
        return None

    def resolve_amount_subtotal(self, info):
        subtotal_lines = self.order_line.filtered(lambda l: not l.is_reward_line)
        return sum(subtotal_lines.mapped('price_total')) - self.amount_delivery

    def resolve_amount_discounts(self, info):
        return self.reward_amount

    def resolve_amount_gift_cards(self, info):
        return sum(self.order_line.filtered(
            lambda l: l.coupon_id and l.coupon_id.program_type and
                      l.coupon_id.program_type == 'gift_card').mapped('price_total'))

    def resolve_coupons(self, info):
        return self.applied_coupon_ids.filtered(lambda c: c.program_type == 'coupons') or None

    def resolve_gift_cards(self, info):
        return self.applied_coupon_ids.filtered(lambda c: c.program_type == 'gift_card') or None

    def resolve_cart_quantity(self, info):
        return self.cart_quantity or None


class InvoiceLine(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    product = graphene.Field(lambda: Product)
    quantity = graphene.Float()
    price_unit = graphene.Float()
    price_subtotal = graphene.Float()
    price_total = graphene.Float()

    def resolve_product(self, info):
        return self.product_id or None


class Invoice(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    partner = graphene.Field(lambda: Partner)
    partner_shipping = graphene.Field(lambda: Partner)
    invoice_date = graphene.String()
    invoice_date_due = graphene.String()
    tax_totals = generic.GenericScalar()
    amount_untaxed = graphene.Float()
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    amount_residual = graphene.Float()
    currency = graphene.Field(lambda: Currency)
    invoice_lines = graphene.List(graphene.NonNull(lambda: InvoiceLine))
    state = InvoiceState()
    invoice_url = graphene.String()
    transactions = graphene.List(graphene.NonNull(lambda: PaymentTransaction))

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_invoice_date(self, info):
        return self.invoice_date or None

    def resolve_invoice_date_due(self, info):
        return self.invoice_date_due or None

    def resolve_tax_totals(self, info):
        return self.tax_totals or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_invoice_lines(self, info):
        return self.invoice_line_ids or None

    def resolve_state(self, info):
        return self.state or None

    def resolve_invoice_url(self, info):
        return self.get_portal_url() or None

    def resolve_transactions(self, info):
        return self.transaction_ids or None


class WishlistItem(OdooObjectType):
    id = graphene.Int(required=True)
    partner = graphene.Field(lambda: Partner)
    product = graphene.Field(lambda: Product)

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_product(self, info):
        return self.product_id or None


class PaymentIcon(OdooObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)
    image = graphene.String()

    def resolve_image(self, info):
        return '/web/image/payment.icon/{}/image'.format(self.id)


class PaymentProvider(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    display_as = graphene.String()
    code = graphene.String()
    payment_icons = graphene.List(graphene.NonNull(lambda: PaymentIcon))

    def resolve_payment_icons(self, info):
        return self.payment_icon_ids or None


class MailingList(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()


class MailingContactSubscription(OdooObjectType):
    id = graphene.Int(required=True)
    mailing_list = graphene.Field(lambda: MailingList)
    opt_out = graphene.Boolean()

    def resolve_mailing_list(self, info):
        return self.list_id or None


class MailingContact(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    email = graphene.String()
    company_name = graphene.String()
    subscription_list = graphene.List(graphene.NonNull(lambda: MailingContactSubscription))

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_industry(self, info):
        return self.industry_id or None

    def resolve_subscription_list(self, info):
        return self.subscription_list_ids or None


class Website(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    company = graphene.Field(lambda: Company)

    def resolve_company(self, info):
        return self.company_id or None


class WebsiteMenu(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    url = graphene.String()
    is_footer = graphene.Boolean()
    is_mega_menu = graphene.Boolean()
    sequence = graphene.Int()
    parent = graphene.Field(lambda: WebsiteMenu)
    childs = graphene.List(graphene.NonNull(lambda: WebsiteMenu))
    images = graphene.List(graphene.NonNull(lambda: WebsiteMenuImage))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_images(self, info):
        return self.menu_image_ids or None


class WebsiteMenuImage(OdooObjectType):
    id = graphene.Int(required=True)
    image = graphene.String()
    tag = graphene.String()
    title = graphene.String()
    subtitle = graphene.String()
    sequence = graphene.Int()
    text_color = graphene.String()
    button_text = graphene.String()
    button_url = graphene.String()

    def resolve_image(self, info):
        return '/web/image/website.menu.image/{}/image'.format(self.id)
