# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class DialogWizard(models.TransientModel):
    _name = 'sales_trip.dialog.wizard'

    title = fields.Char(readonly=1)
    message = fields.Char(readonly=1)

