# -*- coding: utf-8 -*-
# Copyright 2023 ERPGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.invoice import (
    InvoiceSortInput as VSFInvoiceSortInput,
    Invoices as VSFInvoices,
    InvoiceList as VSFInvoiceList,
    InvoiceQuery as VSFInvoiceQuery,
)
from odoo.addons.graphql_cla.schemas.objects import (
    ClaInvoice as Invoice,
)


class Invoices(VSFInvoices):
    invoices = graphene.List(Invoice)


class InvoiceList(VSFInvoiceList):
    class Meta:
        interfaces = (Invoices,)


class InvoiceQuery(VSFInvoiceQuery):
    invoice = graphene.Field(
        Invoice,
        required=True,
        id=graphene.Int(),
    )
    invoices = graphene.Field(
        Invoices,
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        sort=graphene.Argument(VSFInvoiceSortInput, default_value={})
    )

    @staticmethod
    def resolve_invoice(self, info, id):
        res = VSFInvoiceQuery.resolve_invoice(self, info, id)
        return res

    @staticmethod
    def resolve_invoices(self, info, current_page, page_size, sort):
        res = VSFInvoiceQuery.resolve_invoices(self, info, current_page, page_size, sort)
        return InvoiceList(invoices=res.invoices and res.invoices.sudo() or res.invoices, total_count=res.total_count)
