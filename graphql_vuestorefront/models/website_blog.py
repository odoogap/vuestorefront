# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _
from odoo.addons.http_routing.models.ir_http import slugify


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

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
                    prefix = '/blog'
                    rec_slug = slugify(rec.name or '').strip().strip('-')
                    rec.website_slug = '{}/{}-{}'.format(prefix, rec_slug, rec.id)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _compute_website_url(self):
        super(BlogPost, self)._compute_website_url()
        for rec in self:
            if rec.website_slug:
                rec.website_url = rec.website_slug

    def _default_content(self):
        return '<p class="o_default_snippet_text">' + _("Start writing here...") + '</p>'

    name = fields.Char('Title', required=True, translate=True, default='', tracking=True)
    subtitle = fields.Char('Subtitle', translate=True, tracking=True)
    author_id = fields.Many2one('res.partner', 'Author', default=lambda self: self.env.user.partner_id, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    is_published = fields.Boolean(string='Is Published', default=False, tracking=True)
    publish_val = fields.Boolean(string='Publish Value', related='is_published')
    blog_id = fields.Many2one('blog.blog', 'Blog', required=True, ondelete='cascade', tracking=True)
    tag_ids = fields.Many2many('blog.tag', string='Tags')
    content = fields.Text(string='Content', default=_default_content, translate=True, tracking=True)
    website_id = fields.Many2one(related='blog_id.website_id', readonly=True, store=True)
    image_ids = fields.One2many('blog.image', 'post_id', string='Blog Images')

    # creation / update stuff
    create_date = fields.Datetime('Created on', index=True, readonly=True, tracking=True)
    published_date = fields.Datetime('Published Date', tracking=True)
    post_date = fields.Datetime('Publishing date', compute='_compute_post_date', inverse='_set_post_date', store=True,
                                help="The blog post will be visible for your visitors as of this date on the website if it is set as published.",
                                tracking=True)
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True, tracking=True)
    write_date = fields.Datetime('Last Updated on', index=True, readonly=True, tracking=True)
    write_uid = fields.Many2one('res.users', 'Last Contributor', index=True, readonly=True, tracking=True)

    # Website
    website_slug = fields.Char('Website Slug', compute='_compute_website_slug', store=True, readonly=True,
                               translate=True)

    @api.depends('name', 'blog_id.name')
    def _compute_website_slug(self):
        langs = self.env['res.lang'].search([])

        for rec in self:
            for lang in langs:
                rec = rec.with_context(lang=lang.code)

                if not rec.id:
                    rec.website_slug = None
                else:
                    prefix = '/blog'
                    rec_slug = slugify(rec.name or '').strip().strip('-')

                    if rec.blog_id and rec.blog_id.id:
                        blog_slug = slugify(rec.blog_id.name or '').strip().strip('-')
                        rec.website_slug = '{}/{}-{}/{}-{}'.format(prefix, blog_slug, rec.blog_id.id, rec_slug, rec.id)


class BlogImage(models.Model):
    _name = 'blog.image'
    _description = 'Blog Image'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10, index=True)
    image_1920 = fields.Image(required=True)
    image_url = fields.Char(string='Image url', compute='_compute_image_url')
    post_id = fields.Many2one('blog.post', 'Blog Post', index=True, ondelete='cascade')

    def _compute_image_url(self):
        for rec in self:
            if rec.image_1920:
                rec.image_url = '/web/image/blog.image/' + str(rec.id) + '/image_1920'
            else:
                rec.image_url = False
