# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class UnbilledCustomers(models.Model):
    _name = "res.partner.unbilled.customer"
    _table = "res_partner_unbilled_customer_report"
    _auto = False

    id = fields.Integer()
    name = fields.Char(string="Name")
    last_invoice_create_date = fields.Date(string="Last invoice creation date")
    nb_days_without_billing = fields.Integer(string="Nb days without billing")
    last_invoice_year = fields.Integer("Last invoice year")
    payment_term = fields.Char(string="Payment term")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'res_partner_unbilled_customer')
        tools.drop_view_if_exists(self._cr, 'res_partner_unbilled_customer_report')
        # self._cr.execute("""
        #      CREATE OR REPLACE VIEW res_partner_unbilled_customer_report AS (
        #         SELECT cli.id AS id, cli.name, ai.create_date AS invoice_create_date \
        #         FROM account_invoice ai INNER JOIN res_partner cli ON ai.partner_id = cli.id
        #         WHERE ai.id IN
        #             (SELECT MAX(inv.id)
        #                 FROM account_invoice inv
        #                 INNER JOIN res_partner res
        #                 ON inv.partner_id = res.id
        #                 WHERE inv.type = 'out_invoice'
        #                 GROUP BY res.name)
        #         AND ai.create_date <= NOW() - INTERVAL '35 DAY'
        #      )""")

        self._cr.execute("""
             CREATE OR REPLACE VIEW res_partner_unbilled_customer_report AS (
                SELECT cli.id AS id, cli.name, ai.create_date AS last_invoice_create_date, NOW()::date - ai.create_date::date as nb_days_without_billing, \
                    date_part('year', ai.create_date) as last_invoice_year, \
                    pt.name as payment_term \
                FROM account_invoice ai INNER JOIN res_partner cli ON ai.partner_id = cli.id \
                INNER JOIN ir_property ir
                ON cli.id = split_part(ir.res_id, ',', 2)::int AND ir.name = 'property_payment_term_id'
                INNER JOIN account_payment_term pt
                ON split_part(ir.value_reference, ',', 2) = pt.id::text
                WHERE ai.id IN \
                    (SELECT MAX(inv.id) \
                        FROM account_invoice inv \
                        INNER JOIN res_partner res \
                        ON inv.partner_id = res.id \
                        WHERE inv.type = 'out_invoice' \
                        GROUP BY res.name) 
             )""")

