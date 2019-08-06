# -*- coding: utf-8 -*-
from odoo import http

# class SalesTrip(http.Controller):
#     @http.route('/sales_trip/sales_trip/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_trip/sales_trip/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_trip.listing', {
#             'root': '/sales_trip/sales_trip',
#             'objects': http.request.env['sales_trip.sales_trip'].search([]),
#         })

#     @http.route('/sales_trip/sales_trip/objects/<model("sales_trip.sales_trip"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_trip.object', {
#             'object': obj
#         })