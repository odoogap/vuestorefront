# -*- coding: utf-8 -*-
# Copyright 2024 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import requests
from odoo import models, fields, api


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    website_meta_img = fields.Image('Website meta image')
    json_ld = fields.Char('JSON-LD')


class Website(models.Model):
    _name = 'website'
    _inherit = ['website', 'website.seo.metadata']

    vsf_payment_success_return_url = fields.Char(
        'Payment Success Return Url', required=True, translate=True, default='Dummy'
    )
    vsf_payment_error_return_url = fields.Char(
        'Payment Error Return Url', required=True,  translate=True, default='Dummy'
    )
    vsf_mailing_list_id = fields.Many2one('mailing.list', 'Newsletter', domain=[('is_public', '=', True)])
    reset_password_email_template_id = fields.Many2one('mail.template', string='Reset Password')
    order_confirmation_email_template_id = fields.Many2one('mail.template', string='Order confirmation')

    @api.model
    def enable_b2c_reset_password(self):
        """ Enable sign up and reset password on default website """
        website = self.env.ref('website.default_website', raise_if_not_found=False)
        if website:
            website.auth_signup_uninvited = 'b2c'

        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('auth_signup.invitation_scope', 'b2c')
        ICP.set_param('auth_signup.reset_password', True)

    def get_json_ld(self):
        self.ensure_one()
        if self.json_ld:
            return self.json_ld

        website = self.env['website'].get_current_website()
        base_url = website.domain or ''
        if base_url and base_url[-1] == '/':
            base_url = base_url[:-1]

        company = website.company_id

        social_fields = [
            'social_twiter',
            'social_facebook',
            'social_github',
            'social_linkedin',
            'social_youtube',
            'social_instagram',
            'social_tiktok',
        ]

        social = list()
        for social_field in social_fields:
            value = getattr(self, social_field, None)
            if value:
                social.append(value)

        address = {
            "@type": "PostalAddress",
        }
        if company.street:
            address.update({"streetAddress": company.street})
        if company.street2:
            if address.get('streetAddress'):
                address['streetAddress'] += ', ' + company.street2
            else:
                address.update({"streetAddress": company.street2})
        if company.city:
            address.update({"addressLocality": company.city})
        if company.state_id:
            address.update({"addressRegion": company.state_id.name})
        if company.zip:
            address.update({"postalCode": company.zip})
        if company.country_id:
            address.update({"addressCountry": company.country_id.name})

        json_ld = {
           "@context": "https://schema.org",
           "@type": "Organization",
           "name": website.name,
           "url": website.domain,
           "logo": f'{base_url}/web/image/website/{self.id}/logo',
        }

        if social:
            json_ld.update({
                "sameAs": social,
            })

        if company.phone or company.mobile:
            json_ld.update({
                "contactPoint": {
                    "@type": "ContactPoint",
                    "telephone": company.phone or company.mobile,
                }
            })

        json_ld.update({
            "address": address
        })

        return json.dumps(json_ld)


class WebsiteRewrite(models.Model):
    _inherit = 'website.rewrite'

    def _get_vsf_tags(self):
        tags = 'WR%s' % self.id
        return tags

    def _vsf_request_cache_invalidation(self):
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('vsf_cache_invalidation_url', False)
        key = ICP.get_param('vsf_cache_invalidation_key', False)

        if url and key:
            try:
                for website_rewrite in self:
                    tags = website_rewrite._get_vsf_tags()

                    # Make the GET request to the /cache-invalidate
                    requests.get(url, params={'key': key, 'tags': tags}, timeout=5)
            except:
                pass

    def write(self, vals):
        res = super(WebsiteRewrite, self).write(vals)
        self._vsf_request_cache_invalidation()
        return res

    def unlink(self):
        self._vsf_request_cache_invalidation()
        return super(WebsiteRewrite, self).unlink()


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    is_footer = fields.Boolean('Is Footer', default=False)
    menu_image_ids = fields.One2many('website.menu.image', 'menu_id', string='Menu Images')
    is_mega_menu = fields.Boolean(store=True)


class WebsiteMenuImage(models.Model):
    _name = 'website.menu.image'
    _description = 'Website Menu Image'

    def _default_sequence(self):
        menu = self.search([], limit=1, order="sequence DESC")
        return menu.sequence or 0

    menu_id = fields.Many2one('website.menu', 'Website Menu', required=True)
    sequence = fields.Integer(default=_default_sequence)
    image = fields.Image(string='Image', required=True)
    tag = fields.Char('Tag')
    title = fields.Char('Title')
    subtitle = fields.Char('Subtitle')
    text_color = fields.Char('Text Color (Hex)', help='#111000')
    button_text = fields.Char('Button Text')
    button_url = fields.Char('Button URL')
