# -*- coding: utf-8 -*-
from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'
    _order = 'name'

    pos_user_id = fields.Many2one('res.users', string="Assigned user")