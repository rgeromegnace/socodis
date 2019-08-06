# -*- coding: utf-8 -*-

# Copyright 2016-2018 Digitom (<http://www.digitom.com>)

from odoo import api, models


class StockPickingConfirmWizard(models.TransientModel):
    _name = "stock.picking.confirm.wizard"
    _description = "Wizard - Stock Picking Confirm"

    @api.multi
    def confirm_stock_pickings(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        pickings = self.env['stock.picking'].browse(active_ids)
        for picking in pickings:
            picking.validate_picking()
