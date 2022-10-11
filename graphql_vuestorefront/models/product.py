# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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

    def _validate_prod_website_slug(self):
        for product in self.filtered(lambda c: c.website_slug):
            if product.website_slug[0] != "/":
                raise ValidationError(_("Slug should start with /"))

            if not product.website_id:
                res = self.search(
                    [
                        ("website_slug", "=", product.website_slug),
                        ("id", "!=", product.id),
                    ],
                    limit=1,
                )
                if res:
                    raise ValidationError(
                        _(
                            "Slug: (%s) is already in use for other product."
                            % (product.website_slug)
                        )
                    )
            if product.website_id:
                slug_cats = self.search(
                    [
                        ("website_slug", "=", product.website_slug),
                        ("website_id", "=", product.website_id.id),
                        ("id", "!=", product.id),
                    ]
                )
                for prod in slug_cats:
                    if product.website_id.id == prod.website_id.id:
                        raise ValidationError(
                            _(
                                "Duplicate Slugs within a website are not allowed. Slug: (%s) is already in use for the product: (%s) and same website: (%s)."
                                % (
                                    product.website_slug,
                                    prod.name,
                                    prod.website_id.name,
                                )
                            )
                        )
    
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
            product.variant_attribute_value_ids = [(6, 0, attribute_values.ids)]

    variant_attribute_value_ids = fields.Many2many('product.attribute.value',
                                                   'product_template_variant_product_attribute_value_rel',
                                                   compute='_compute_variant_attribute_value_ids',
                                                   store=True, readonly=True)
    # website_slug = fields.Char('Website Slug', compute='_compute_website_slug', store=True, readonly=True,
    #                            translate=True)
    website_slug = fields.Char("Website Slug", translate=True, store=True, copy=False)
    public_categ_slug_ids = fields.Many2many('product.public.category',
                                             'product_template_product_public_category_slug_rel',
                                             compute='_compute_public_categ_slug_ids',
                                             store=True, readonly=True)
    json_ld = fields.Char('JSON-LD')

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if vals.get("website_slug") or vals.get("website_id"):
            self._validate_prod_website_slug()
        elif not vals.get("website_slug") or not vals.get("website_id"):
            self._validate_prod_website_slug()
        self.env["invalidate.cache"].create_invalidate_cache(self._name, self.ids, vals)
        return res

    def unlink(self):
        self.env["invalidate.cache"].create_invalidate_cache(self._name, self.ids)
        return super(ProductTemplate, self).unlink()

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        """ Add discount value and percentage based """
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        discount = 0
        discount_perc = 0

        if combination_info['has_discounted_price']:
            discount = combination_info['list_price'] - combination_info['price']
            discount_perc = combination_info['list_price'] and (discount * 100 / combination_info['list_price']) or 0

        combination_info.update({
            'discount': round(discount, 2),
            'discount_perc': int(discount_perc),
        })

        return combination_info

    def get_json_ld(self):
        self.ensure_one()
        if self.json_ld:
            return self.json_ld

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

        # Get list of images
        images = list()
        if self.image_1920:
            images.append('%s/web/image/product.product/%s/image' % (base_url, self.id))

        website = self.env['website'].get_current_website()

        json_ld = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": self.display_name,
            "image": images,
            "offers": {
                "@type": "Offer",
                "url": "%s/product/%s" % (base_url, slug(self)),
                "priceCurrency": self.currency_id.name,
                "price": self.list_price,
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock",
                "seller": {
                    "@type": "Organization",
                    "name": website and website.display_name or self.env.user.company_id.display_name
                }
            }
        }

        if self.description_sale:
            json_ld.update({"description": self.description_sale})

        if self.default_code:
            json_ld.update({"sku": self.default_code})

        return json.dumps(json_ld)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_json_ld(self):
        self.ensure_one()
        if self.json_ld:
            return self.json_ld

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

        # Get list of images
        images = list()
        if self.image_1920:
            images.append('%s/web/image/product.product/%s/image' % (base_url, self.id))

        website = self.env['website'].get_current_website()

        json_ld = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": self.display_name,
            "image": images,
            "offers": {
                "@type": "Offer",
                "url": "%s/product/%s" % (base_url, slug(self)),
                "priceCurrency": self.currency_id.name,
                "price": self.list_price,
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock",
                "seller": {
                    "@type": "Organization",
                    "name": website and website.display_name or self.env.user.company_id.display_name
                }
            }
        }

        if self.description_sale:
            json_ld.update({"description": self.description_sale})

        if self.default_code:
            json_ld.update({"sku": self.default_code})

        return json.dumps(json_ld)


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _validate_cat_website_slug(self):
        for category in self.filtered(lambda c: c.website_slug):
            if category.website_slug[0] != "/":
                raise ValidationError(_("Slug should start with /"))
            if not category.website_id:
                res = self.search(
                    [
                        ("website_slug", "=", category.website_slug),
                        ("id", "!=", category.id),
                    ],
                    limit=1,
                )
                if res:
                    raise ValidationError(
                        _(
                            "Slug: (%s) is already in use for other category."
                            % (category.website_slug)
                        )
                    )
            if category.website_id:
                slug_cats = self.search(
                    [
                        ("website_slug", "=", category.website_slug),
                        ("website_id", "=", category.website_id.id),
                        ("id", "!=", category.id),
                    ]
                )
                for cat in slug_cats:
                    if category.website_id.id == cat.website_id.id:
                        raise ValidationError(
                            _(
                                "Duplicate Slugs within a website are not allowed. Slug: (%s) is already in use for the category: (%s) and same website: (%s)."
                                % (
                                    category.website_slug,
                                    cat.name,
                                    cat.website_id.name,
                                )
                            )
                        )

    website_slug = fields.Char('Website Slug', translate=True, copy=False)

    @api.model
    def create(self, vals):
        rec = super(ProductPublicCategory, self).create(vals)

        if rec.website_slug:
            rec._validate_cat_website_slug()
        else:
            rec.website_slug = "/category/{}".format(rec.id)

        return rec

    def write(self, vals):
        res = super(ProductPublicCategory, self).write(vals)
        if vals.get("website_slug") or vals.get("website_id"):
            self._validate_cat_website_slug()
        elif not vals.get("website_slug") or not vals.get("website_id"):
            self._validate_cat_website_slug()
        self.env["invalidate.cache"].create_invalidate_cache(self._name, self.ids, vals)
        return res

    def unlink(self):
        self.env["invalidate.cache"].create_invalidate_cache(self._name, self.ids)
        return super(ProductPublicCategory, self).unlink()