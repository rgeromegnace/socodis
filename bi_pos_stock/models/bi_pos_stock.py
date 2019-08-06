# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning
import random
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class pos_config(models.Model):
	_inherit = 'pos.config'
	
	pos_display_stock = fields.Boolean(string='Display Stock in POS')
	pos_stock_type = fields.Selection([('onhand', 'Qty on Hand'), ('incoming', 'Incoming Qty'), ('outgoing', 'Outgoing Qty'), ('available', 'Qty Available'), ('with_not_confirmed', 'Qty Available with not confirm sale')], string='Stock Type', help='Seller can display Different stock type in POS.')
	pos_allow_order = fields.Boolean(string='Allow POS Order When Product is Out of Stock')
	pos_deny_order = fields.Char(string='Deny POS Order When Product Qty is goes down to')   
	
	show_stock_location = fields.Selection([
		('all', 'All Warehouse'),
		('specific', 'Current Session Warehouse'),
		], string='Show Stock Of', default='all')
		

class stock_quant(models.Model):
	_inherit = 'stock.quant'


	@api.multi
	def get_stock_location_qty(self, location):
		res = {}
		product_ids = self.env['product.product'].search([])
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			if len(quants) > 1:
				quantity = 0.0
				for quant in quants:
					quantity += quant.quantity
				res.update({product.id : quantity})
			else:
				res.update({product.id : quants.quantity})
		# print("ressssssssssssssssssssssss",res)
		return [res]

	def get_single_product(self,product, location):
		res = []
		pro = self.env['product.product'].browse(product)
		# print("selfffffffffffffffffffffffffffffffff",pro)
		quants = self.env['stock.quant'].search([('product_id', '=', pro.id),('location_id', '=', location['id'])])
		if len(quants) > 1:
			quantity = 0.0
			for quant in quants:
				quantity += quant.quantity
			res.append([pro.id, quantity])
		else:
			res.append([pro.id, quants.quantity])
		# print("ressssssssssssssssssssssss",res)
		return res



class product(models.Model):
	_inherit = 'product.product'

	available_quantity = fields.Float('Available Quantity')
	not_confiremd_qty_available  = fields.Float('Not confirmed sale Available Quantity',compute='sale_not_confirmed_quant')


	@api.multi
	def sale_not_confirmed_quant(self):
		dt = date.today()
		res = {}
		qty=0.0
		product_qty = 0.0
		final_quantity =0.0
		used_products =[]
		remained_products = []
		final_products = []
		in_pro =[]
		session = self.env['pos.session'].search([('user_id', '=',self.env.uid),('state', 'in',['opened'])])
		config_id = session.config_id
		location = config_id.stock_location_id.id
		# print("sessionssssssssssssssssssssssss",session,config_id,location)
		product_ids = self.env['product.product'].search([])
		# orders = self.env['sale.order'].search([('state', 'in',['draft','sent'])])
		# order1 = self.env['sale.order'].search([('created_date', '=',dt)])
		# print("productsssssssssss",self)
		for pro in self:
			if pro not in remained_products:
					remained_products.append(pro)
			line = self.env['sale.order.line'].search([('product_id', '=',pro.id)])	
			qty= 0
			qty1 =0
			for i in line:
				if i.product_id not in used_products:
					used_products.append(i.product_id)
				order = i.order_id
				sd = order.date_order
				d1=datetime.strptime(sd,DEFAULT_SERVER_DATETIME_FORMAT).date()
				warehouse = self.env['stock.picking.type'].search([('warehouse_id', '=',order.warehouse_id.id),('code', '=','outgoing')])
				loc = warehouse.default_location_src_id.id
				if order.state in ['draft','sent'] and  d1 == dt:
					if i.product_id not in in_pro:
						in_pro.append(i.product_id)
					quants = self.env['stock.quant'].search([('product_id', '=', pro.id),('location_id', '=', location)])
					#qty2 += i.product_uom_qty
					if config_id.show_stock_location == 'specific':
						if location == loc:
							qty += i.product_uom_qty
							if len(quants) > 1:
								quantity = 0.0
								for quant in quants:
									quantity += quant.quantity
								final_quantity = quantity - qty
								pro.not_confiremd_qty_available = final_quantity
								# pro.update({'not_confiremd_qty_available' : final_quantity})

							else:
								final_quantity = quants.quantity - qty
								pro.not_confiremd_qty_available = final_quantity
							# pro.update({'not_confiremd_qty_available': final_quantity})

					if config_id.show_stock_location == 'all':
						qty1 += i.product_uom_qty
						product_qty = i.product_id.qty_available
						final_quantity = product_qty - qty1
						pro.not_confiremd_qty_available = final_quantity
						# pro.update({'not_confiremd_qty_available' : final_quantity})
				

				if order.state in ['done','sale','cancelled'] and  d1 == dt:
					not_in = [x for x in used_products if x not in in_pro]
					for pro1 in not_in:
						quants = self.env['stock.quant'].search([('product_id', '=', pro1.id),('location_id', '=', location)])
						if config_id.show_stock_location == 'specific':
							if location == loc:
								if len(quants) > 1:
									quantity = 0.0
									for quant in quants:
										quantity += quant.quantity
									pro1.not_confiremd_qty_available = quantity
								else:
									pro1.not_confiremd_qty_available = quants.quantity

						if config_id.show_stock_location == 'all':
								pro1.not_confiremd_qty_available = i.product_id.qty_available
		# final_products = remained_products - used_products
		final_products = [x for x in remained_products if x not in used_products]
		for pro in final_products:
			if config_id.show_stock_location == 'specific':
				quants = self.env['stock.quant'].search([('product_id', '=', pro.id),('location_id', '=', location)])
				if len(quants) > 1:
					quantity = 0.0
					for quant in quants:
						quantity += quant.quantity
					pro.not_confiremd_qty_available = quantity
				else:
					pro.not_confiremd_qty_available = quants.quantity

			if config_id.show_stock_location == 'all':
					pro.not_confiremd_qty_available = pro.qty_available
	
			

	@api.multi
	def get_stock_location_avail_qty(self, location):
		res = {}
		product_ids = self.env['product.product'].search([])
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			outgoing = self.env['stock.move'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			incoming = self.env['stock.move'].search([('product_id', '=', product.id),('location_dest_id', '=', location['id'])])
			qty=0.0
			product_qty = 0.0
			incoming_qty = 0.0
			if len(quants) > 1:
				for quant in quants:
					qty += quant.quantity

				if len(outgoing) > 0:
					for quant in outgoing:
						if quant.state not in ['done']:
							product_qty += quant.product_qty

				if len(incoming) > 0:
					for quant in incoming:
						if quant.state not in ['done']:
							incoming_qty += quant.product_qty
					product.available_quantity = qty-product_qty + incoming_qty
					res.update({product.id : qty-product_qty + incoming_qty})
			else:
				if not quants:
					if len(outgoing) > 0:
						for quant in outgoing:
							if quant.state not in ['done']:
								product_qty += quant.product_qty

					if len(incoming) > 0:
						for quant in incoming:
							if quant.state not in ['done']:
								incoming_qty += quant.product_qty
					product.available_quantity = qty-product_qty + incoming_qty
					res.update({product.id : qty-product_qty + incoming_qty})
				else:
					if len(outgoing) > 0:
						for quant in outgoing:
							if quant.state not in ['done']:
								product_qty += quant.product_qty

					if len(incoming) > 0:
						for quant in incoming:
							if quant.state not in ['done']:
								incoming_qty += quant.product_qty
					product.available_quantity = quants.quantity - product_qty + incoming_qty
					res.update({product.id : quants.quantity - product_qty + incoming_qty})
		return [res]
	


	
