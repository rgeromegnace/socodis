# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.addons import decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = 'product.product'
    _order = 'name'

    pmpa = fields.Float('PMPA', digits=dp.get_precision('Product Price'))

