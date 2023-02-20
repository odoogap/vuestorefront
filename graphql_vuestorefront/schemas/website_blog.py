# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.http import request
from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum,
    BlogBlog,
    BlogPost,
    BlogTag,
    BlogTagCategory,
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'id ASC'

    return sorting


# ----------------------------- #
#           Blog Post           #
# ----------------------------- #

class BlogPostFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    website_slug = graphene.String()


class BlogPostSortInput(graphene.InputObjectType):
    id = SortEnum()


class BlogPosts(graphene.Interface):
    blog_posts = graphene.List(BlogPost)
    total_count = graphene.Int(required=True)


class BlogPostList(graphene.ObjectType):
    class Meta:
        interfaces = (BlogPosts,)


class BlogPostQuery(graphene.ObjectType):
    blog_post = graphene.Field(
        BlogPost,
        id=graphene.Int(),
        website_slug=graphene.String(default_value=None),
    )
    blog_posts = graphene.Field(
        BlogPosts,
        filter=graphene.Argument(BlogPostFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(BlogPostSortInput, default_value={})
    )

    @staticmethod
    def resolve_blog_post(self, info, id=None, website_slug=None):
        env = info.context['env']
        BlogPost = env['blog.post'].sudo()
        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            blog_post = BlogPost.search(domain, limit=1)
        elif website_slug:
            domain += [('website_slug', '=', website_slug)]
            blog_post = BlogPost.search(domain, limit=1)
        else:
            blog_post = BlogPost

        return blog_post

    @staticmethod
    def resolve_blog_posts(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = get_search_order(sort)
        vsf_blog_blog_id = website.vsf_blog_blog_id
        domain = [
            ('is_published', '=', True), '|', ('blog_id', '=', vsf_blog_blog_id.id), ('website_id', '=', website.id)
        ]

        if search:
            for srch in search.split(" "):
                domain += ['|', '|', '|', ('name', 'ilike', srch), ('subtitle', 'ilike', srch),
                           ('tag_ids.name', 'ilike', srch), ('website_meta_keywords', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        if filter.get('website_slug'):
            domain += [('website_slug', '=', filter['website_slug'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        BlogPost = env['blog.post'].sudo()
        total_count = BlogPost.search_count(domain)
        blog_posts = BlogPost.search(domain, limit=page_size, offset=offset, order=order)
        return BlogPostList(blog_posts=blog_posts, total_count=total_count)


# ----------------------------- #
#            Blog Tag           #
# ----------------------------- #

class BlogTagFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)


class BlogTagSortInput(graphene.InputObjectType):
    id = SortEnum()


class BlogTags(graphene.Interface):
    blog_tags = graphene.List(BlogTag)
    total_count = graphene.Int(required=True)


class BlogTagList(graphene.ObjectType):
    class Meta:
        interfaces = (BlogTags,)


class BlogTagQuery(graphene.ObjectType):
    blog_tag = graphene.Field(
        BlogTag,
        id=graphene.Int(),
    )
    blog_tags = graphene.Field(
        BlogTags,
        filter=graphene.Argument(BlogTagFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(BlogTagSortInput, default_value={})
    )

    @staticmethod
    def resolve_blog_tag(self, info, id=None):
        env = info.context['env']
        BlogTag = env['blog.tag'].sudo()
        domain = []

        if id:
            domain += [('id', '=', id)]
            blog_tag = BlogTag.search(domain, limit=1)
        else:
            blog_tag = BlogTag

        return blog_tag

    @staticmethod
    def resolve_blog_tags(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        website = env['website'].get_current_website()
        request.website = website
        order = get_search_order(sort)
        vsf_blog_blog_id = website.vsf_blog_blog_id
        domain = ['|', ('post_ids.blog_id', '=', vsf_blog_blog_id.id), ('post_ids.website_id', '=', website.id)]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        BlogTag = env['blog.tag'].sudo()
        total_count = BlogTag.search_count(domain)
        blog_tags = BlogTag.search(domain, limit=page_size, offset=offset, order=order)
        return BlogTagList(blog_tags=blog_tags, total_count=total_count)


# ----------------------------- #
#       Blog Tag Category       #
# ----------------------------- #

class BlogTagCategoryFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)


class BlogTagCategorySortInput(graphene.InputObjectType):
    id = SortEnum()


class BlogTagCategories(graphene.Interface):
    blog_tag_categories = graphene.List(BlogTagCategory)
    total_count = graphene.Int(required=True)


class BlogTagCategoryList(graphene.ObjectType):
    class Meta:
        interfaces = (BlogTagCategories,)


class BlogTagCategoryQuery(graphene.ObjectType):
    blog_tag_category = graphene.Field(
        BlogTagCategory,
        id=graphene.Int(),
    )
    blog_tag_categories = graphene.Field(
        BlogTagCategories,
        filter=graphene.Argument(BlogTagCategoryFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(BlogTagCategorySortInput, default_value={})
    )

    @staticmethod
    def resolve_blog_tag_category(self, info, id=None):
        env = info.context['env']
        BlogTagCategory = env['blog.tag.category'].sudo()
        domain = []

        if id:
            domain += [('id', '=', id)]
            blog_tag_category = BlogTagCategory.search(domain, limit=1)
        else:
            blog_tag_category = BlogTagCategory

        return blog_tag_category

    @staticmethod
    def resolve_blog_tag_categories(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = []

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        BlogTagCategory = env['blog.tag.category'].sudo()
        total_count = BlogTagCategory.search_count(domain)
        blog_tag_categories = BlogTagCategory.search(domain, limit=page_size, offset=offset, order=order)
        return BlogTagCategoryList(blog_tag_categories=blog_tag_categories, total_count=total_count)
