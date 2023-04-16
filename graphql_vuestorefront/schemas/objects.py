# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
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
    company_name = graphene.String()
    company_reg_no = graphene.String()

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

    def resolve_company_name(self, info):
        return self.parent_id and self.parent_id.name or None

    def resolve_company_reg_no(self, info):
        return self.parent_id and self.parent_id.company_reg_no or None


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
    first_variant = graphene.Int(description='Specific to use in Product Template')
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
    acquirer = graphene.String()
    acquirer_reference = graphene.String()
    company = graphene.Field(lambda: Partner)
    customer = graphene.Field(lambda: Partner)
    state = PaymentTransactionState()

    def resolve_payment(self, info):
        return self.payment_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_acquirer(self, info):
        return self.acquirer_id.name or None

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
    warning_stock = graphene.String()
    gift_card = graphene.Field(lambda: GiftCard)
    coupon = graphene.Field(lambda: Coupon)

    def resolve_product(self, info):
        return self.product_id or None

    def resolve_quantity(self, info):
        return self.product_uom_qty or None

    def resolve_gift_card(self, info):
        return self.gift_card_id or None

    def resolve_coupon(self, info):
        coupons = self.order_id.applied_coupon_ids.filtered(
            lambda c: self.product_id and c.discount_line_product_id and c.discount_line_product_id.id == self.product_id.id)
        return coupons and coupons[0] or None


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

    def resolve_price(self, info):
        website = self.env['website'].get_current_website()
        request.website = website
        order = website.sale_get_order(force_create=True)
        return self.rate_shipment(order)['price'] if self.free_over else self.fixed_price


class Order(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    partner = graphene.Field(lambda: Partner)
    partner_shipping = graphene.Field(lambda: Partner)
    partner_invoice = graphene.Field(lambda: Partner)
    date_order = graphene.String()
    totals_json = generic.GenericScalar()
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

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_partner_invoice(self, info):
        return self.partner_invoice_id or None

    def resolve_date_order(self, info):
        return self.date_order or None

    def resolve_totals_json(self, info):
        return self.tax_totals_json or None

    def resolve_shipping_method(self, info):
        return self.carrier_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_order_lines(self, info):
        return self.order_line or None

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

    def resolve_coupons(self, info):
        return self.applied_coupon_ids or None

    def resolve_amount_subtotal(self, info):
        subtotal_lines = self.order_line.filtered(lambda l: not l.gift_card_id and not l.is_reward_line)
        return sum(subtotal_lines.mapped('price_total')) - self.amount_delivery

    def resolve_amount_discounts(self, info):
        return sum(self._get_reward_lines().mapped('price_total'))

    def resolve_amount_gift_cards(self, info):
        return sum(self.order_line.filtered(lambda l: l.gift_card_id).mapped('price_total'))


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
    totals_json = generic.GenericScalar()
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

    def resolve_totals_json(self, info):
        return self.tax_totals_json or None

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
    id = graphene.ID()
    name = graphene.String(required=True)
    image = graphene.String()

    def resolve_image(self, info):
        return '/web/image/payment.icon/{}/image'.format(self.id)


class PaymentAcquirer(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    display_as = graphene.String()
    provider = graphene.String()
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


# ----------------------------- #
#         Website Page          #
# ----------------------------- #

class WebsitePage(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    website_url = graphene.String()
    is_published = graphene.Boolean()
    publishing_date = graphene.String()
    website = graphene.Field(lambda: Website)
    content = graphene.String()

    def resolve_website_url(self, info):
        return self.url or None

    def resolve_publishing_date(self, info):
        return self.date_publish or None

    def resolve_website(self, info):
        return self.website_id or None


# ----------------------------- #
#         Website Blog          #
# ----------------------------- #

class BlogBlog(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    subtitle = graphene.String()
    content = graphene.String()
    blog_posts = graphene.List(graphene.NonNull(lambda: BlogPost))
    blog_post_count = graphene.Int()
    website = graphene.Field(lambda: Website)
    website_slug = graphene.String()

    def resolve_content(self, info):
        return self.content or None

    def resolve_blog_posts(self, info):
        return self.blog_post_ids or None

    def resolve_website(self, info):
        return self.website_id or None


class BlogTagCategory(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    tags = graphene.List(graphene.NonNull(lambda: BlogTag))

    def resolve_tags(self, info):
        return self.tag_ids or None


class BlogTag(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    category = graphene.Field(lambda: BlogTagCategory)
    posts = graphene.List(graphene.NonNull(lambda: BlogPost))

    def resolve_category(self, info):
        return self.category_id or None

    def resolve_posts(self, info):
        return self.post_ids or None


class BlogImage(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    sequence = graphene.Int()
    image = graphene.String()
    post = graphene.Field(lambda: BlogPost)

    def resolve_image(self, info):
        return self.image_url or None

    def resolve_post(self, info):
        return self.post_id or None


class BlogPost(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    subtitle = graphene.String()
    tags = graphene.List(graphene.NonNull(lambda: BlogTag))
    author = graphene.Field(lambda: Partner)
    author_image = graphene.String()
    author_name = graphene.String()
    is_published = graphene.Boolean()
    content = graphene.String()
    teaser = graphene.String()
    teaser_manual = graphene.String()
    blog = graphene.Field(lambda: BlogBlog)
    website = graphene.Field(lambda: Website)
    images = graphene.List(graphene.NonNull(lambda: BlogImage))
    website_slug = graphene.String()
    # Creation / Update Stuff
    create_date = graphene.String()
    published_date = graphene.String()
    publishing_date = graphene.String()
    created_by = graphene.Field(lambda: User)
    last_update_on = graphene.String()
    last_contributor = graphene.Field(lambda: User)
    # SEO Website
    is_seo_optimized = graphene.Boolean()
    website_meta_title = graphene.String()
    website_meta_description = graphene.String()
    website_meta_keywords = graphene.String()
    website_meta_og_img = graphene.String()
    seo_name = graphene.String()

    def resolve_tags(self, info):
        return self.tag_ids or None

    def resolve_author(self, info):
        return self.author_id or None

    def resolve_author_image(self, info):
        return '/web/image/res.partner/{}/image_128'.format(self.author_id.id)

    def resolve_blog(self, info):
        return self.blog_id or None

    def resolve_website(self, info):
        return self.website_id or None

    def resolve_images(self, info):
        return self.image_ids or None

    def resolve_publishing_date(self, info):
        return self.post_date or None

    def resolve_created_by(self, info):
        return self.create_uid or None

    def resolve_last_update_on(self, info):
        return self.write_date or None

    def resolve_last_contributor(self, info):
        return self.write_uid or None


# ----------------------------- #
#          Website CMS          #
# ----------------------------- #

class CmsCollection(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    subtitle = graphene.String()
    content = graphene.String()
    contents = graphene.List(graphene.NonNull(lambda: CmsContent))
    content_count = graphene.Int()
    website = graphene.Field(lambda: Website)
    website_slug = graphene.String()

    def resolve_content(self, info):
        return self.content or None

    def resolve_contents(self, info):
        return self.content_ids or None

    def resolve_website(self, info):
        return self.website_id or None


class CmsImage(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    sequence = graphene.Int()
    image = graphene.String()
    content = graphene.Field(lambda: CmsContent)

    def resolve_image(self, info):
        return self.image_url or None

    def resolve_content(self, info):
        return self.content_id or None


class CmsContent(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    subtitle = graphene.String()
    author = graphene.Field(lambda: Partner)
    author_image = graphene.String()
    author_name = graphene.String()
    is_published = graphene.Boolean()
    content = graphene.String()
    teaser = graphene.String()
    teaser_manual = graphene.String()
    collection = graphene.Field(lambda: CmsCollection)
    website = graphene.Field(lambda: Website)
    images = graphene.List(graphene.NonNull(lambda: CmsImage))
    website_slug = graphene.String()
    # Creation / Update Stuff
    create_date = graphene.String()
    published_date = graphene.String()
    publishing_date = graphene.String()
    created_by = graphene.Field(lambda: User)
    last_update_on = graphene.String()
    last_contributor = graphene.Field(lambda: User)
    # SEO Website
    is_seo_optimized = graphene.Boolean()
    website_meta_title = graphene.String()
    website_meta_description = graphene.String()
    website_meta_keywords = graphene.String()
    website_meta_og_img = graphene.String()
    seo_name = graphene.String()

    def resolve_author(self, info):
        return self.author_id or None

    def resolve_author_image(self, info):
        return '/web/image/res.partner/{}/image_128'.format(self.author_id.id)

    def resolve_collection(self, info):
        return self.collection_id or None

    def resolve_website(self, info):
        return self.website_id or None

    def resolve_images(self, info):
        return self.image_ids or None

    def resolve_publishing_date(self, info):
        return self.post_date or None

    def resolve_created_by(self, info):
        return self.create_uid or None

    def resolve_last_update_on(self, info):
        return self.write_date or None

    def resolve_last_contributor(self, info):
        return self.write_uid or None
