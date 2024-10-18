# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from odoo.osv import expression
from datetime import timedelta
from odoo import models, fields, api, tools, _
from odoo.tools.float_utils import float_round
from odoo.addons.http_routing.models.ir_http import slug, slugify
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _graphql_get_search_order(self, sort):
        sorting = ''
        for field, val in sort.items():
            if sorting:
                sorting += ', '
            if field == 'price':
                sorting += 'list_price %s' % val.value
            elif field == 'popular':
                sorting += 'sales_count_30_days %s' % val.value
            elif field == 'newest':
                sorting += 'create_date %s' % val.value
            else:
                sorting += '%s %s' % (field, val.value)

        # Add id as last factor, so we can consistently get the same results
        if sorting:
            sorting += ', id ASC'
        else:
            sorting = 'id ASC'

        return sorting

    @api.model
    def _graphql_get_search_domain(self, search, **kwargs):
        env = self.env

        # Only get published products
        domains = [
            env['website'].get_current_website().sale_product_domain(),
            [('is_published', '=', True)],
        ]

        # Filter with ids
        if kwargs.get('ids', False):
            domains.append([('id', 'in', kwargs['ids'])])

        # Filter with Category ID
        if kwargs.get('category_id', False):
            domains.append([('public_categ_ids', 'child_of', kwargs['category_id'])])

        # Filter with Category Slug
        if kwargs.get('category_slug', False):
            domains.append([('public_categ_slug_ids.website_slug', '=', kwargs['category_slug'])])

        # Filter With Name
        if kwargs.get('name', False):
            name = kwargs['name']
            for n in name.split(" "):
                domains.append([('name', 'ilike', n)])

        if search:
            for srch in search.split(" "):
                domains.append([
                    '|', '|', ('name', 'ilike', srch), ('description_sale', 'like', srch), ('default_code', 'like', srch)])

        partial_domain = domains.copy()

        # Product Price Filter
        if kwargs.get('min_price', False):
            domains.append([('list_price', '>=', float(kwargs['min_price']))])
        if kwargs.get('max_price', False):
            domains.append([('list_price', '<=', float(kwargs['max_price']))])

        # Deprecated: filter with Attribute Value
        if kwargs.get('attribute_value_id', False):
            domains.append([('attribute_line_ids.value_ids', 'in', kwargs['attribute_value_id'])])

        # Filter with Attribute Value
        if kwargs.get('attrib_values', False):
            attributes = {}
            attributes_domain = []

            for value in kwargs['attrib_values']:
                try:
                    value = value.split('-')
                    if len(value) != 2:
                        continue

                    attribute_id = int(value[0])
                    attribute_value_id = int(value[1])
                except ValueError:
                    continue

                if attribute_id not in attributes:
                    attributes[attribute_id] = []

                attributes[attribute_id].append(attribute_value_id)

            for key, value in attributes.items():
                attributes_domain.append([('attribute_line_ids.value_ids', 'in', value)])

            attributes_domain = expression.AND(attributes_domain)
            domains.append(attributes_domain)

        return expression.AND(domains), expression.AND(partial_domain)

    def _compute_json_ld(self):
        env = self.env
        website = env['website'].get_current_website()
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        if base_url and base_url[-1:] == '/':
            base_url = base_url[:-1]

        for product in self:
            # Get list of images
            images = list()
            if product.image_1920:
                images.append(f'{base_url}/web/image/product.product/{product.id}/image')

            json_ld = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": product.display_name,
                "image": images,
                "offers": {
                    "@type": "Offer",
                    "url": f"{website.domain or ''}/product/{slug(product)}",
                    "priceCurrency": product.currency_id.name,
                    "price": product.list_price,
                    "itemCondition": "https://schema.org/NewCondition",
                    "availability": "https://schema.org/InStock",
                    "seller": {
                        "@type": "Organization",
                        "name": website and website.display_name or product.env.user.company_id.display_name
                    }
                }
            }

            if product.description_sale:
                json_ld.update({"description": product.description_sale})

            if product.default_code:
                json_ld.update({"sku": product.default_code})

            product.json_ld = json.dumps(json_ld)

    def _get_public_categ_slug(self, category_ids, category):
        category_ids.append(category.id)

        if category.parent_id:
            category_ids = self._get_public_categ_slug(category_ids, category.parent_id)

        return category_ids

    @api.depends('public_categ_ids')
    def _compute_public_categ_slug_ids(self):
        """ To allow search of website_slug on parent categories """
        cr = self.env.cr

        for product in self:
            category_ids = []

            for category in product.public_categ_ids:
                category_ids = product._get_public_categ_slug(category_ids, category)

            cr.execute("""
                DELETE FROM product_template_product_public_category_slug_rel
                WHERE product_template_id=%s;
            """, (product.id,))

            for category_id in list(dict.fromkeys(category_ids)):
                cr.execute("""
                    INSERT INTO product_template_product_public_category_slug_rel(product_template_id, product_public_category_id)
                    VALUES(%s, %s);
                """, (product.id, category_id,))

    @api.depends('name')
    def _compute_website_slug(self):
        langs = self.env['res.lang'].search([])

        for product in self:
            for lang in langs:
                product = product.with_context(lang=lang.code)

                if not product.id:
                    product.website_slug = None
                else:
                    prefix = '/product'
                    slug_name = slugify(product.name or '').strip().strip('-')
                    product.website_slug = '{}/{}-{}'.format(prefix, slug_name, product.id)

    @api.depends('product_variant_ids')
    def _compute_variant_attribute_value_ids(self):
        """
        Used to filter attribute values on the website.
        This method computes a list of attribute values from variants of published products.
        This will ensure that the available attribute values on the website filtering will return results.
        By default, Odoo only shows attributes that will return results but doesn't consider that a particular
        attribute value may not have a variant.
        """
        for product in self:
            variants = product.product_variant_ids
            attribute_values = variants.\
                mapped('product_template_attribute_value_ids').\
                mapped('product_attribute_value_id')
            attribute_values += variants.\
                mapped('valid_product_template_attribute_line_ids').\
                mapped('value_ids')
            product.variant_attribute_value_ids = [(6, 0, attribute_values.ids)]

    def _compute_sales_count_30_days(self):
        date_30_days_ago = fields.Datetime.now() - timedelta(days=30)
        done_states = self.env['sale.report'].sudo()._get_done_states()
        domain = [
            ('state', 'in', done_states),
            ('date', '>=', date_30_days_ago),
        ]

        sale_groups = self.env['sale.report'].sudo().read_group(
            domain,
            ['product_id', 'product_uom_qty'],
            ['product_id'],
        )

        sale_count_map = {group['product_id'][0]: group['product_uom_qty'] for group in sale_groups}

        for product in self:
            product_id = product.product_variant_id.id
            count = sale_count_map.get(product_id, 0)
            product.sales_count_30_days = float_round(count, precision_rounding=product.uom_id.rounding)

    variant_attribute_value_ids = fields.Many2many('product.attribute.value',
                                                   'product_template_variant_product_attribute_value_rel',
                                                   compute='_compute_variant_attribute_value_ids',
                                                   store=True, readonly=True)
    website_slug = fields.Char('Website Slug', compute='_compute_website_slug', store=True, readonly=True,
                               translate=True)
    public_categ_slug_ids = fields.Many2many('product.public.category',
                                             'product_template_product_public_category_slug_rel',
                                             compute='_compute_public_categ_slug_ids',
                                             store=True, readonly=True)
    sales_count_30_days = fields.Float('Sales Count 30 Days', compute='_compute_sales_count_30_days', store=True,
                                       readonly=True)

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        self.env['invalidate.cache'].create_invalidate_cache(self._name, self.ids)
        return res

    def unlink(self):
        self.env['invalidate.cache'].create_invalidate_cache(self._name, self.ids)
        return super(ProductTemplate, self).unlink()

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, parent_combination=False,
                              only_template=False):
        """ Add discount value and percentage based """
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, parent_combination=parent_combination,
            only_template=only_template)

        discount = 0
        discount_perc = 0
        if combination_info['has_discounted_price'] and product_id:
            discount = combination_info['list_price'] - combination_info['price']
            discount_perc = combination_info['list_price'] and (discount * 100 / combination_info['list_price']) or 0

        combination_info.update({
            'discount': round(discount, 2),
            'discount_perc': int(round(discount_perc, 2)),
        })

        return combination_info

    @api.model
    def recalculate_products_popularity(self):
        self.search([])._compute_sales_count_30_days()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_json_ld(self):
        env = self.env
        website = env['website'].get_current_website()
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        if base_url and base_url[-1:] == '/':
            base_url = base_url[:-1]

        for product in self:
            # Get list of images
            images = list()
            if product.image_1920:
                images.append(f'{base_url}/web/image/product.product/{product.id}/image')

            json_ld = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": product.display_name,
                "image": images,
                "offers": {
                    "@type": "Offer",
                    "url": f"{website.domain or ''}/product/{slug(product)}",
                    "priceCurrency": product.currency_id.name,
                    "price": product.list_price,
                    "itemCondition": "https://schema.org/NewCondition",
                    "availability": "https://schema.org/InStock",
                    "seller": {
                        "@type": "Organization",
                        "name": website and website.display_name or product.env.user.company_id.display_name
                    }
                }
            }

            if product.description_sale:
                json_ld.update({"description": product.description_sale})

            if product.default_code:
                json_ld.update({"sku": product.default_code})

            product.json_ld = json.dumps(json_ld)


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _compute_json_ld(self):
        website = self.env['website'].get_current_website()
        base_url = website.domain or ''
        if base_url and base_url[-1] == '/':
            base_url = base_url[:-1]

        for category in self:
            json_ld = {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "url": f'{base_url}{category.website_slug}',
                "name": category.display_name,
            }

            category.json_ld = json.dumps(json_ld)

    def _validate_website_slug(self):
        for category in self.filtered(lambda c: c.website_slug):
            if category.website_slug[0] != '/':
                raise ValidationError(_('Slug should start with /'))

            if self.search([('website_slug', '=', category.website_slug), ('id', '!=', category.id)], limit=1):
                raise ValidationError(_('Slug is already in use: {}'.format(category.website_slug)))

    website_slug = fields.Char('Website Slug', translate=True, copy=False)
    attribute_ids = fields.Many2many('product.attribute', string='Filtering Attributes')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductPublicCategory, self).create(vals_list)

        for rec in res:
            if rec.website_slug:
                rec._validate_website_slug()
            else:
                rec.website_slug = '/category/{}'.format(rec.id)

        return res

    def write(self, vals):
        res = super(ProductPublicCategory, self).write(vals)
        if vals.get('website_slug', False):
            self._validate_website_slug()
        self.env['invalidate.cache'].create_invalidate_cache(self._name, self.ids)
        return res

    def unlink(self):
        self.env['invalidate.cache'].create_invalidate_cache(self._name, self.ids)
        return super(ProductPublicCategory, self).unlink()


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    visibility = fields.Selection(related='attribute_id.visibility', store=True, readonly=True)
