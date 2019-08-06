# -*- coding: utf-8 -*-

# Copyright 2016-2018 Digitom (<http://www.digitom.com>)

from odoo import api, models, fields, _


class UnbilledCustomersReportWizard(models.TransientModel):
    _name = "contact.unbilled.customers.report.wizard"
    _description = "Set nb days"

    compute_since_days = fields.Selection([
        (0, 'Since more than 35 days'),
        (1, 'Since more than a specific number of days')
    ], string="Unbilled customers", help="Choose to list unbilled customers since 35 days or a specific number of days.", default=0)
    since_days = fields.Integer('Nb days', help="Choose since number of days", default=35)

    def open_table(self):
        if self.compute_since_days:
            tree_view_id = self.env.ref('kyimport.view_partner_unbilled_customer_tree').id
            domain = [('nb_days_without_billing', '>=', self.since_days)]
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree')],
                'view_mode': 'tree',
                'name': _('Customers'),
                'res_model': 'res.partner.unbilled.customer',
                'domain': domain,
                # 'context': dict(self.env.context, to_date=self.date, company_owned=True),
            }
            return action
        else:
            return self.env.ref('kyimport.partner_unbilled_customer_action').read()[0]
