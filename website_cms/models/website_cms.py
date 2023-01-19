# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re

from odoo import api, models, fields, _
from odoo.addons.http_routing.models.ir_http import slugify, slug
from odoo.addons.website.tools import text_from_html
from odoo.tools.json import scriptsafe as json_scriptsafe


class CmsCollection(models.Model):
    _name = 'cms.collection'
    _description = 'CMS Collection'
    _inherit = [
        'mail.thread',
        'website.multi.mixin',
        'website.cover_properties.mixin',
        'website.searchable.mixin',
    ]
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True, tracking=True)
    subtitle = fields.Char(string='Subtitle', translate=True, tracking=True)
    content = fields.Text(string='Collection Content', translate=True, tracking=True)
    content_ids = fields.One2many('cms.content', 'collection_id', string='Contents')
    content_count = fields.Integer(string='Content Count', compute='_compute_content_count')
    active = fields.Boolean(string='Active', default=True, tracking=True)

    # Website
    website_slug = fields.Char('Website Slug', compute='_compute_website_slug', store=True, readonly=True,
                               translate=True)

    @api.depends('name')
    def _compute_website_slug(self):
        langs = self.env['res.lang'].search([])

        for rec in self:
            for lang in langs:
                rec = rec.with_context(lang=lang.code)

                if not rec.id:
                    rec.website_slug = None
                else:
                    prefix = '/cms'
                    rec_slug = slugify(rec.name or '').strip().strip('-')
                    rec.website_slug = '{}/{}-{}'.format(prefix, rec_slug, rec.id)

    @api.depends('content_ids')
    def _compute_content_count(self):
        for rec in self:
            rec.content_count = len(rec.content_ids)

    def write(self, vals):
        res = super(CmsCollection, self).write(vals)
        if 'active' in vals:

            # Archive/Unarchive a Collection does it on its Contents, too
            content_ids = self.env['cms.content'].with_context(active_test=False).search([
                ('collection_id', 'in', self.ids)
            ])
            for rec in content_ids:
                rec.active = vals['active']
        return res


class CmsImage(models.Model):
    _name = 'cms.image'
    _description = 'CMS Image'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10, index=True)
    image_1920 = fields.Image(required=True)
    image_url = fields.Char(string='Image url', compute='_compute_image_url')
    content_id = fields.Many2one('cms.content', 'Content', index=True, ondelete='cascade')

    def _compute_image_url(self):
        for rec in self:
            if rec.image_1920:
                rec.image_url = '/web/image/cms.image/' + str(rec.id) + '/image_1920'
            else:
                rec.image_url = False


class CmsContent(models.Model):
    _name = 'cms.content'
    _description = 'CMS Content'
    _inherit = [
        'mail.thread',
        'website.seo.metadata',
        'website.published.multi.mixin',
        'website.cover_properties.mixin',
        'website.searchable.mixin'
    ]
    _order = 'id DESC'

    def _compute_website_url(self):
        super(CmsContent, self)._compute_website_url()
        for rec in self:
            if rec.website_slug:
                rec.website_url = rec.website_slug

    def _default_content(self):
        return '<p class="o_default_snippet_text">' + _("Start writing here...") + '</p>'

    name = fields.Char(string='Title', required=True, translate=True, default='', tracking=True)
    subtitle = fields.Char(string='Subtitle', translate=True, tracking=True)
    author_id = fields.Many2one('res.partner', 'Author', default=lambda self: self.env.user.partner_id, tracking=True)
    author_avatar = fields.Binary(related='author_id.image_128', string='Avatar', readonly=False)
    author_name = fields.Char(related='author_id.display_name', string="Author Name", readonly=False, store=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    is_published = fields.Boolean(string='Is Published', default=False, tracking=True)
    publish_val = fields.Boolean(string='Publish Value', related='is_published')
    content = fields.Text(string='Content', default=_default_content, translate=True, tracking=True)
    teaser = fields.Text(string='Teaser', compute='_compute_teaser', inverse='_set_teaser')
    teaser_manual = fields.Text(string='Teaser Content')
    collection_id = fields.Many2one('cms.collection', 'Collection', required=True, ondelete='cascade', tracking=True)
    website_id = fields.Many2one(related='collection_id.website_id', store=True, tracking=True)
    image_ids = fields.One2many('cms.image', 'content_id', string='Images')

    # Creation / Update stuff
    create_date = fields.Datetime(string='Created on', index=True, readonly=True, tracking=True)
    published_date = fields.Datetime('Published Date', tracking=True)
    post_date = fields.Datetime(string='Publishing date', compute='_compute_post_date', inverse='_set_post_date',
                                store=True,
                                help="The blog post will be visible for your visitors "
                                     "as of this date on the website if it is set as published.", tracking=True)
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True, tracking=True)
    write_date = fields.Datetime(string='Last Updated on', index=True, readonly=True, tracking=True)
    write_uid = fields.Many2one('res.users', 'Last Contributor', index=True, readonly=True, tracking=True)

    # Website
    website_slug = fields.Char('Website Slug', compute='_compute_website_slug', store=True, readonly=True,
                               translate=True, tracking=True)

    @api.depends('name', 'collection_id.name')
    def _compute_website_slug(self):
        langs = self.env['res.lang'].search([])

        for rec in self:
            for lang in langs:
                rec = rec.with_context(lang=lang.code)

                if not rec.id:
                    rec.website_slug = None
                else:
                    prefix = '/cms'
                    rec_slug = slugify(rec.name or '').strip().strip('-')

                    if rec.collection_id and rec.collection_id.id:
                        collection_slug = slugify(rec.collection_id.name or '').strip().strip('-')
                        rec.website_slug = '{}/{}-{}/{}-{}'.format(
                            prefix, collection_slug, rec.collection_id.id, rec_slug, rec.id
                        )

    @api.depends('content', 'teaser_manual')
    def _compute_teaser(self):
        for rec in self:
            if rec.teaser_manual:
                rec.teaser = rec.teaser_manual
            else:
                content = text_from_html(rec.content)
                content = re.sub('\\s+', ' ', content).strip()
                rec.teaser = content[:200] + '...'

    def _set_teaser(self):
        for rec in self:
            rec.teaser_manual = rec.teaser

    @api.depends('create_date', 'published_date')
    def _compute_post_date(self):
        for rec in self:
            if rec.published_date:
                rec.post_date = rec.published_date
            else:
                rec.post_date = rec.create_date

    def _set_post_date(self):
        for rec in self:
            rec.published_date = rec.post_date
            if not rec.published_date:
                rec._write(dict(post_date=rec.create_date))  # dont trigger inverse function

    def _default_website_meta(self):
        res = super(CmsContent, self)._default_website_meta()
        res['default_opengraph']['og:description'] = res['default_twitter']['twitter:description'] = self.subtitle
        res['default_opengraph']['og:type'] = 'article'
        res['default_opengraph']['article:published_time'] = self.post_date
        res['default_opengraph']['article:modified_time'] = self.write_date
        # background-image might contain single quotes eg `url('/my/url')`
        res['default_opengraph']['og:image'] = res['default_twitter']['twitter:image'] = json_scriptsafe.loads(self.cover_properties).get('background-image', 'none')[4:-1].strip("'")
        res['default_opengraph']['og:title'] = res['default_twitter']['twitter:title'] = self.name
        res['default_meta_description'] = self.subtitle
        return res
