# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from openerp import models, fields, api, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    sale_order_operations = fields.Selection([('draft','Quotations'),
                            ('confirm', 'Confirm'),('paid', 'Paid')], "Operation", default="draft")
    sale_order_last_days = fields.Char("Load Orders to Last days")
    sale_order_record_per_page = fields.Char("Record Per Page")
    paid_amount_product = fields.Many2one('product.product', string='Paid Amount Product', domain=[('available_in_pos', '=', True)])
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        if partner.get('property_product_pricelist') :
            price_list_id = int(partner.get('property_product_pricelist'))
            partner.update({'property_product_pricelist': price_list_id})
        return super(ResPartner, self).create_from_ui(partner)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: