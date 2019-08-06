# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    trip_template_ids = fields.One2many('sales_trip.trip_template','commercial_id', string='Trip templates')
    billing_type = fields.Selection(
        [(1, 'Comptant'),
         (2, 'FCA'),
         (3, 'En compte')],
        'Billing type',
        default=1
    )

    trip_ids = fields.Many2many('sales_trip.trip', string="Trips")