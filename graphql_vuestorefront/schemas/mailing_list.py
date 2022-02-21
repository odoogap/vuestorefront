# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.addons.website_mass_mailing.controllers.main import MassMailController


class NewsletterSubscribe(graphene.Mutation):
    class Arguments:
        email = graphene.String()

    subscribed = graphene.Boolean()

    @staticmethod
    def mutate(self, info, email):
        list_id = int(info.context["env"]['ir.config_parameter'].sudo().set_param('vsf_mailing_list_id', 0))
        if list_id:
            MassMailController().subscribe(list_id, email)
            return NewsletterSubscribe(subscribed=True)

        return NewsletterSubscribe(subscribed=False)


class NewsletterSubscribeMutation(graphene.ObjectType):
    newsletter_subscribe = NewsletterSubscribe.Field(description='Subscribe to newsletter.')
