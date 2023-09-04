# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.country import (
    CountryFilterInput as VSFCountryFilterInput,
    CountrySortInput as VSFCountrySortInput,
    Countries as VSFCountries,
    CountryList as VSFCountryList,
    CountryQuery as VSFCountryQuery,
)
from odoo.addons.graphql_custom.schemas.objects import (
    CustomCountry as Country,
)


class Countries(VSFCountries):
    countries = graphene.List(Country)


class CountryList(VSFCountryList):
    class Meta:
        interfaces = (Countries,)


class CountryQuery(VSFCountryQuery):
    country = graphene.Field(
        Country,
        required=True,
        id=graphene.Int(),
    )
    countries = graphene.Field(
        Countries,
        filter=graphene.Argument(VSFCountryFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(VSFCountrySortInput, default_value={})
    )

    @staticmethod
    def resolve_country(self, info, id):
        res = VSFCountryQuery.resolve_country(self, info, id)
        return res

    @staticmethod
    def resolve_countries(self, info, filter, current_page, page_size, search, sort):
        res = VSFCountryQuery.resolve_countries(self, info, filter, current_page, page_size, search, sort)
        return CountryList(countries=res.countries, total_count=res.total_count)
