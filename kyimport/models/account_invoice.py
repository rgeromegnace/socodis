# -*- coding: utf-8 -*-

from odoo import api, models, fields
from functools import reduce
from odoo.tools.float_utils import float_round as round

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _order = 'name'

    tax_include_price = fields.Monetary(string='Taxe include Price',
                                        readonly=True, compute='_compute_tax_include_price')

    @api.multi
    def _compute_tax_include_price(self):
        currency = None
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id

        for record in self:
            #record.tax_include_price = round(record.price_unit * reduce((lambda x,y: (1 + x.amount) * (1 + y.amount)), record.invoice_line_tax_ids))
            record.tax_include_price = currency.round(record.price_unit * (1+record.invoice_line_tax_ids.amount/100))


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _order = 'name'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = {
            'user_id': self.partner_id.user_id.id or self.env.uid
        }

        self.update(values)

