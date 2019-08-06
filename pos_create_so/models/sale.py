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
from openerp import fields, models, api, _

class sale_order(models.Model):
    _inherit = "sale.order"

    @api.model
    def create_sales_order(self, orderline, customer_id, location_id, journals):
       sale_pool = self.env['sale.order']
       prod_pool = self.env['product.product']
       sale_line_pool = self.env['sale.order.line']
       if customer_id:
           customer_id = int(customer_id)
           partner_records = self.get_res_partner_record(customer_id)
           payment_term_id = None
           if partner_records is not None:
               for partner_record in partner_records:
                   payment_term_id = partner_record.property_payment_term_id.id
           #sale = {'partner_id': customer_id, 'partner_invoice_id': customer_id, 'partner_shipping_id': customer_id}
           sale = {'partner_id': customer_id, 'partner_invoice_id': customer_id, 'partner_shipping_id': customer_id, 'payment_term_id': payment_term_id, 'workflow_process_id': 1}
           new = sale_pool.new({'partner_id': customer_id})
           new.onchange_partner_id()
           sale_id = sale_pool.create(sale)
           for line in orderline:
               prod_rec = prod_pool.browse(line['product_id'])
               line.update({'order_id': sale_id.id,
                            'name': prod_rec.name or False,
                            'product_id': prod_rec.id,
                            'product_uom_qty': line['qty'],
                            'discount': line.get('discount')})
               new_prod = sale_line_pool.new({'product_id': prod_rec.id})
               prod = new_prod.product_id_change()
               line.update(prod)
               line.update({'price_unit': line['price_unit']});
               taxes = [x.id for x in prod_rec.taxes_id]
               if taxes:
                   line.update({'tax_id': [(6, 0, taxes)]})
               line.pop('domain')
               line.update({'product_uom': prod_rec.uom_id.id})
               sale_line_pool.create(line)
               
           if self._context.get('confirm'):
               sale_id.action_confirm()
           if self._context.get('paid'):
               sale_id.action_confirm()
               inv_id = sale_id.action_invoice_create()
               if not self.generate_invoice(inv_id, journals):
                   return False
               if not self.delivery_order(sale_id, location_id):
                   return False
               sale_id.action_done()
       return (sale_id.id,sale_id.name)

    @api.model
    def get_res_partner_record(self, id):
        """Retourne l'enregistrement associé à l'id client"""
        print(sale_order.get_res_partner_record.__name__)

        records = None

        records = self.env['res.partner'].search([['id', '=', id]])

        return records

    @api.model
    def generate_invoice(self, inv_id, journals):
        account_invoice = self.env['account.invoice'].browse(inv_id)
        if account_invoice:
            account_invoice.action_invoice_open()
            account_payment_obj = self.env['account.payment']
            for journal in journals:
                account_journal_obj= self.env['account.journal'].browse(journal.get('journal_id'))
                if account_journal_obj:
                    payment_id = account_payment_obj.create({
                                               'payment_type': 'inbound',
                                               'partner_id': account_invoice.partner_id.id,
                                               'partner_type': 'customer',
                                               'journal_id': account_journal_obj.id or False,
                                               'amount': journal.get('amount'),
                                               'payment_method_id': account_journal_obj.inbound_payment_method_ids.id,
                                               'invoice_ids': [(6, 0, [account_invoice.id])],
                                               })
                    payment_id.post()
            return True
        return False

    def delivery_order(self, sale_id, location_id):
        picking_id = sale_id.picking_ids
#         if picking_id.pack_operation_product_ids and location_id:
#             picking_id.pack_operation_product_ids.write({'location_id':location_id})
        if picking_id.move_lines and location_id:
            picking_id.move_lines.write({'location_id':location_id})
        if picking_id:
            picking_id.action_confirm()
            picking_id.force_assign()
            picking_id.button_validate()
            stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_ids', '=', picking_id.id)], limit=1).process()
            if stock_transfer_id:
                stock_transfer_id.process()
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: