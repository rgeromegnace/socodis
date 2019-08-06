# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    phone2 = fields.Char("Téléphone 2")
    fax = fields.Char("Fax")
    siret = fields.Char("Siret")
    #import_sap_listprice_id = fields.Integer("SAP listprice id")

