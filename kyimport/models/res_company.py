# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    _order = 'name'

    iban = fields.Char("IBAN")
    fax = fields.Char("Fax")
    cell = fields.Char("Cell")


