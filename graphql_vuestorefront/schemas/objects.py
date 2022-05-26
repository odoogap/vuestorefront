# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _

from werkzeug import urls

from odoo.addons.graphql_base import OdooObjectType
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import AccessError
from odoo.http import request


# --------------------- #
#       ENUMS           #
# --------------------- #

AddressType = graphene.Enum('AddressType', [('Contact', 'contact'), ('InvoiceAddress', 'invoice'),
                                            ('DeliveryAddress', 'delivery'), ('OtherAddress', 'other'),
                                            ('PrivateAddress', 'private')])

OrderStage = graphene.Enum('OrderStage', [('Quotation', 'draft'), ('QuotationSent', 'sent'),
                                          ('SalesOrder', 'sale'), ('Locked', 'done'), ('Cancelled', 'cancel')])

InvoiceStatus = graphene.Enum('InvoiceStatus', [('UpsellingOpportunity', 'upselling'), ('FullyInvoiced', 'invoiced'),
                                                ('ToInvoice', 'to invoice'), ('NothingtoInvoice', 'no')])

InvoiceState = graphene.Enum('InvoiceState', [('Draft', 'draft'), ('Open', 'open'), ('Paid', 'paid'),
                                              ('Cancelled', 'cancel')])

InventoryAvailability = graphene.Enum('InventoryAvailability', [
    ('SellRegardlessOfInventory', 'never'), ('ShowInventoryOnWebsiteAndPreventSalesIfNotEnoughStock', 'always'),
    ('ShowInventoryBelowAThresholdAndPreventSalesIfNotEnoughStock', 'threshold'),
    ('ShowProductSpecificNotifications', 'custom')
])


class SortEnum(graphene.Enum):
    ASC = 'ASC'
    DESC = 'DESC'


# --------------------- #
#      Functions        #
# --------------------- #

def get_document_with_check_access(model, domain, order=None, limit=20, offset=0,
                                   error_msg='This document does not exist.'):
    document = model.search(domain, order=order, limit=limit, offset=offset)
    document_sudo = document.sudo()
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


def product_is_in_wishlist(env, product):
    website = env['website'].get_current_website()
    request.website = website
    return product._is_in_wishlist()


def get_product_pricing_info(env, product):
    website = env['website'].get_current_website()
    pricelist = website.get_current_pricelist()
    return product._get_combination_info_variant(pricelist=pricelist)


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
    image = graphene.String()

    def resolve_states(self, info):
        return self.state_ids or None

    def resolve_image(self, info):
        return '/web/image/res.country/{}/image'.format(self.id)


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
    address_type = AddressType()
    billing_address = graphene.Field(lambda: Partner)
    is_company = graphene.Boolean(required=True)
    company = graphene.Field(lambda: Partner)
    contacts = graphene.List(graphene.NonNull(lambda: Partner))
    signup_token = graphene.String()
    signup_valid = graphene.String()
    parent_id = graphene.Field(lambda: Partner)

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
    image = graphene.String()
    medium_image = graphene.String()
    small_image = graphene.String()
    products = graphene.List(graphene.NonNull(lambda: Product))

    def resolve_parent(self, info):
        return self.parent_id or None

    def resolve_childs(self, info):
        return self.child_id or None

    def resolve_slug(self, info):
        return self.slug or slug(self)

    def resolve_image(self, info):
        return '/web/image/product.public.category/{}/image'.format(self.id)

    def resolve_medium_image(self, info):
        return '/web/image/product.public.category/{}/image_medium'.format(self.id)

    def resolve_small_image(self, info):
        return '/web/image/product.public.category/{}/image_small'.format(self.id)

    def resolve_products(self, info):
        return self.product_tmpl_ids or None


class AttributeValue(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    html_color = graphene.String()
    search = graphene.String()
    price_extra = graphene.Float(description='Not use in the return Attributes List of the Products Query')
    attribute = graphene.Field(lambda: Attribute)
    display_type = graphene.String()

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
    type = graphene.String()
    values = graphene.List(graphene.NonNull(lambda: AttributeValue))

    def resolve_values(self, info):
        return self.value_ids or None


class ProductImage(OdooObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    image = graphene.String()

    def resolve_id(self, info):
        return self.id or None

    def resolve_image(self, info):
        return '/web/image/product.image/{}/image'.format(self.id)


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
    thumbnail = graphene.String()
    categories = graphene.List(graphene.NonNull(lambda: Category))
    inventory_availability = InventoryAvailability()
    available_threshold = graphene.String(
        description='Related W/Availability: Show inventory below a threshold and prevent sales if not enough stock'
    )
    custom_message = graphene.String(description='Related W/Availability: Show product-specific notifications')
    is_in_stock = graphene.Boolean()
    is_in_wishlist = graphene.Boolean()
    media_gallery = graphene.List(graphene.NonNull(lambda: ProductImage))
    qty = graphene.Float()
    slug = graphene.String()
    website_price = graphene.Float()
    website_public_price = graphene.Float()
    website_price_difference = graphene.Float()
    alternative_products = graphene.List(graphene.NonNull(lambda: Product))
    accessory_products = graphene.List(graphene.NonNull(lambda: Product))
    # Specific to use in Product Variant
    combination_info_variant = generic.GenericScalar(description='Specific to Product Variant')
    variant_price = graphene.Float(description='Specific to Product Variant')
    variant_price_after_discount = graphene.Float(description='Specific to Product Variant')
    variant_has_discounted_price = graphene.Boolean(description='Specific to Product Variant')
    price_extra = graphene.Float(description='Specific to Product Variant')
    variant_attribute_values = graphene.List(graphene.NonNull(lambda: AttributeValue),
                                             description='Specific to Product Variant')
    product_template = graphene.Field(lambda: Product, description='Specific to Product Variant')
    # Specific to use in Product Template
    combination_info = generic.GenericScalar(description='Specific to Product Template')
    price = graphene.Float(description='Specific to Product Template')
    attribute_values = graphene.List(graphene.NonNull(lambda: AttributeValue),
                                     description='Specific to Product Template')
    product_variants = graphene.List(graphene.NonNull(lambda: Product), description='Specific to Product Template')
    first_variant = graphene.Int(description='Specific to use in Product Template')

    def resolve_type_id(self, info):
        if self.type == 'product':
            return 'simple'
        else:
            return 'configurable'

    def resolve_visibility(self, info):
        if self.website_published:
            return 1
        else:
            return 0

    def resolve_status(self, info):
        if self.sudo().qty_available > 0:
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
        return '/web/image/{}/{}/image'.format(self._name, self.id)

    def resolve_small_image(self, info):
        return '/web/image/{}/{}/image_small'.format(self._name, self.id)

    def resolve_thumbnail(self, info):
        return '/web/image/{}/{}/image_medium'.format(self._name, self.id)

    def resolve_categories(self, info):
        return self.public_categ_ids or None

    def resolve_available_threshold(self, info):
        return self.available_threshold or None

    def resolve_custom_message(self, info):
        return self.custom_message or None

    def resolve_is_in_stock(self, info):
        return bool(self.sudo().qty_available > 0)

    def resolve_is_in_wishlist(self, info):
        env = info.context["env"]
        is_in_wishlist = product_is_in_wishlist(env, self)
        return bool(is_in_wishlist)

    def resolve_media_gallery(self, info):
        return self.product_image_ids or None

    def resolve_qty(self, info):
        return self.sudo().qty_available

    def resolve_slug(self, info):
        return self.slug or slug(self)

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

    def resolve_price_extra(self, info):
        return self.price_extra or None

    def resolve_variant_attribute_values(self, info):
        return self.attribute_value_ids or None

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
        return self.attribute_line_ids.mapped('value_ids') or None

    def resolve_product_variants(self, info):
        return self.product_variant_ids or None

    def resolve_first_variant(self, info):
        return self.product_variant_id or None


class Payment(OdooObjectType):
    id = graphene.Int()
    name = graphene.String()
    amount = graphene.Float()
    payment_date = graphene.String()
    memo = graphene.String()
    payment_transaction = graphene.Field(lambda: PaymentTransaction)

    def resolve_payment_date(self, info):
        return self.payment_date or None

    def resolve_memo(self, info):
        return self.communication or None

    def resolve_payment_transaction(self, info):
        return self.payment_transaction_id or None


class PaymentTransaction(OdooObjectType):
    id = graphene.Int()
    reference = graphene.String()
    order = graphene.Field(lambda: Order)
    amount = graphene.Float()
    currency = graphene.Field(lambda: Currency)
    fees = graphene.Float()
    partner = graphene.Field(lambda: Partner)
    acquirer = graphene.Field(lambda: PaymentAcquirer)
    acquirer_reference = graphene.String()
    payment_token = graphene.String()

    def resolve_reference(self, info):
        return self.reference or None

    def resolve_order(self, info):
        return self.sale_order_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_fees(self, info):
        return self.fees or None

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_acquirer(self, info):
        return self.acquirer_id or None

    def resolve_acquirer_reference(self, info):
        return self.acquirer_reference or None

    def resolve_payment_token(self, info):
        return self.payment_token_id.name or None


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

    def resolve_product(self, info):
        return self.product_id or None

    def resolve_quantity(self, info):
        return self.product_uom_qty or None


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
    amount_untaxed = graphene.Float()
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    amount_delivery = graphene.Float()
    shipping_method = graphene.Field(lambda: ShippingMethod)
    currency = graphene.Field(lambda: Currency)
    order_lines = graphene.List(graphene.NonNull(lambda: OrderLine))
    website_order_line = graphene.List(graphene.NonNull(lambda: OrderLine))
    stage = OrderStage()
    order_url = graphene.String()
    transactions = graphene.List(graphene.NonNull(lambda: PaymentTransaction))
    transaction_count = graphene.Int()
    customer_reference = graphene.String()
    invoices = graphene.List(graphene.NonNull(lambda: Invoice))
    invoice_status = InvoiceStatus()
    invoice_count = graphene.Int()

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_partner_invoice(self, info):
        return self.partner_invoice_id or None

    def resolve_date_order(self, info):
        return self.date_order or None

    def resolve_shipping_method(self, info):
        return self.carrier_id or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_order_lines(self, info):
        return self.order_line or None

    def resolve_stage(self, info):
        return self.state or None

    def resolve_order_url(self, info):
        return self.get_share_url() or None

    def resolve_transactions(self, info):
        return self.payment_tx_ids or None

    def resolve_transaction_count(self, info):
        return self.payment_transaction_count or None

    def resolve_customer_reference(self, info):
        return self.client_order_ref or None

    def resolve_invoices(self, info):
        return self.invoice_ids or None


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
    number = graphene.String()
    partner = graphene.Field(lambda: Partner)
    partner_shipping = graphene.Field(lambda: Partner)
    invoice_date = graphene.String()
    invoice_date_due = graphene.String()
    amount_untaxed = graphene.Float()
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    amount_residual = graphene.Float()
    currency = graphene.Field(lambda: Currency)
    invoice_lines = graphene.List(graphene.NonNull(lambda: InvoiceLine))
    state = InvoiceState()
    invoice_url = graphene.String()
    payments = graphene.List(graphene.NonNull(lambda: Payment))

    def resolve_partner(self, info):
        return self.partner_id or None

    def resolve_partner_shipping(self, info):
        return self.partner_shipping_id or None

    def resolve_invoice_date(self, info):
        return self.date_invoice or None

    def resolve_invoice_date_due(self, info):
        return self.date_due or None

    def resolve_amount_residual(self, info):
        return self.residual or None

    def resolve_currency(self, info):
        return self.currency_id or None

    def resolve_invoice_lines(self, info):
        return self.invoice_line_ids or None

    def resolve_state(self, info):
        return self.state or None

    def resolve_invoice_url(self, info):
        return self.get_share_url()

    def resolve_payments(self, info):
        return self.payment_ids or None


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
    payment_icons = graphene.List(graphene.NonNull(lambda: PaymentIcon))

    def resolve_payment_icons(self, info):
        return self.payment_icon_ids or None
