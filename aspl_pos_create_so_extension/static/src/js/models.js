odoo.define('aspl_pos_create_so_extension.models', function (require) {
"use strict";

	var models = require('point_of_sale.models');
	var rpc = require('web.rpc');
	var core = require('web.core');

	var _t = core._t;

    models.load_models({
        model: 'res.country.state',
        fields: [],
        context: [],
        loaded: function(self, states){
            self.states = [];
            _.each(states, function(state){
                self.states.push({
                    id: state.id,
                    value: state.name
                });
            });
        },
    });
    models.load_models({
        model: 'res.country',
        fields: [],
        context: [],
        loaded: function(self, countries){
            self.countries = [];
            _.each(countries, function(country){
                self.countries.push({
                    id: country.id,
                    value: country.name
                });
            });
        },
    });

    models.load_fields("res.partner", ['property_product_pricelist']);
    models.load_fields("product.product", ['type', 'invoice_policy']);
    models.load_fields("res.users", ['display_own_sales_order']);

    var _super_Order = models.Order.prototype;
	models.Order = models.Order.extend({
	    initialize: function(attr,options){
	        var self = this;
	        var res = _super_Order.initialize.call(this, attr, options);
	        this.set({
	            'sale_order_name': false,
	            'order_id': false,
	            'shipping_address': false,
	            'invoice_address': false,
	            'sale_note': false,
	            'inv_id': false,
	            'sale_order_date': false,
	            'edit_quotation': false,
	            'paying_sale_order': false,
	            'sale_order_pay': false,
	            'sale_order_requested_date': false,
	        });
	        $('.js_edit_quotation').hide();
	    },
	    set_sale_order_name: function(name){
			this.set('sale_order_name', name);
		},
		get_sale_order_name: function(){
			return this.get('sale_order_name');
		},
		export_for_printing: function(){
            var orders = _super_Order.export_for_printing.call(this);
            var new_val = {
            	sale_order_name: this.get_sale_order_name() || false,
            	sale_note: this.get_sale_note() || '',

            };
            $.extend(orders, new_val);
            return orders;
        },
        set_sequence:function(sequence){
        	this.set('sequence',sequence);
        },
        get_sequence:function(){
        	return this.get('sequence');
        },
        set_order_id: function(order_id){
            this.set('order_id', order_id);
        },
        get_order_id: function(){
            return this.get('order_id');
        },
        set_amount_paid: function(amount_paid) {
            this.set('amount_paid', amount_paid);
        },
        get_amount_paid: function() {
            return this.get('amount_paid');
        },
        set_amount_return: function(amount_return) {
            this.set('amount_return', amount_return);
        },
        get_amount_return: function() {
            return this.get('amount_return');
        },
        set_amount_tax: function(amount_tax) {
            this.set('amount_tax', amount_tax);
        },
        get_amount_tax: function() {
            return this.get('amount_tax');
        },
        set_amount_total: function(amount_total) {
            this.set('amount_total', amount_total);
        },
        get_amount_total: function() {
            return this.get('amount_total');
        },
        set_company_id: function(company_id) {
            this.set('company_id', company_id);
        },
        get_company_id: function() {
            return this.get('company_id');
        },
        set_date_order: function(date_order) {
            this.set('date_order', date_order);
        },
        get_date_order: function() {
            return this.get('date_order');
        },
        set_pos_reference: function(pos_reference) {
            this.set('pos_reference', pos_reference)
        },
        set_shipping_address: function(val){
            this.set('shipping_address', val);
        },
        get_shipping_address: function() {
            return this.get('shipping_address');
        },
        set_invoice_address: function(val){
            this.set('invoice_address', val);
        },
        get_invoice_address: function() {
            return this.get('invoice_address');
        },
        set_sale_note: function(val){
            this.set('sale_note', val);
        },
        get_sale_note: function() {
            return this.get('sale_note');
        },
        set_inv_id: function(inv_id) {
            this.set('inv_id', inv_id)
        },
        get_inv_id: function() {
            return this.get('inv_id');
        },
        set_sale_order_date: function(sale_order_date) {
            this.set('sale_order_date', sale_order_date)
        },
        get_sale_order_date: function() {
            return this.get('sale_order_date');
        },
        set_sale_order_requested_date: function(sale_order_requested_date) {
            this.set('sale_order_requested_date', sale_order_requested_date)
        },
        get_sale_order_requested_date: function() {
            return this.get('sale_order_requested_date');
        },
        set_edit_quotation: function(edit_quotation) {
            this.set('edit_quotation', edit_quotation)
        },
        get_edit_quotation: function() {
            return this.get('edit_quotation');
        },
        set_paying_sale_order: function(paying_sale_order) {
            this.set('paying_sale_order', paying_sale_order)
        },
        get_paying_sale_order: function() {
            return this.get('paying_sale_order');
        },
        set_sale_order_pay: function(sale_order_pay) {
            this.set('sale_order_pay', sale_order_pay)
        },
        get_sale_order_pay: function() {
            return this.get('sale_order_pay');
        },
	});

	var _super_posmodel = models.PosModel;
	models.PosModel = models.PosModel.extend({
		load_server_data: function(){
			var self = this;
			var product_index = _.findIndex(this.models, function (model) {
                return model.model === "product.product";
            });
            var product_model = this.models[product_index];
            product_model.domain = [['sale_ok','=',true]];
            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });
            var partner_model = this.models[partner_index];
            partner_model.domain = [];
			var loaded = _super_posmodel.prototype.load_server_data.call(this);
			return loaded.then(function(){
				var date = new Date();
				var domain;
				var start_date;
				self.domain_sale_order = [];
				if(date){
                    if(self.config.sale_order_last_days){
                        date.setDate(date.getDate() - self.config.sale_order_last_days);
                    }
                    start_date = date.toJSON().slice(0,10);
                    self.domain_sale_order.push(['create_date' ,'>=', start_date]);
                } else {
                    domain = [];
                }
                self.domain_sale_order.push(['state','not in',['cancel']]);
                var params = {
					model: 'sale.order',
					method: 'search_read',
					domain: self.domain_sale_order
				}
				rpc.query(params, {async: false}).then(function(orders){
					self.db.add_sale_orders(orders);
					if(self.user.display_own_sales_order){
						var user_orders = [];
						orders.map(function(sale_order){
							if(sale_order.user_id[0] == self.user.id){
								user_orders.push(sale_order);
							}
						});
						orders = user_orders;
					}
					orders.map(function(sale_order){
						if(sale_order.date_order){
							var dt = new Date(new Date(sale_order.date_order) + "GMT");
						   	var n = dt.toLocaleDateString(); 
						   	    var crmon = self.addZero(dt.getMonth()+1);
						   	    var crdate = self.addZero(dt.getDate());
						   	    var cryear = dt.getFullYear();
						   	    var crHour = self.addZero(dt.getHours());
						   	    var crMinute = self.addZero(dt.getMinutes());
						   	    var crSecond = self.addZero(dt.getSeconds());
						   	 sale_order.date_order = cryear + '/' + crmon +'/'+ crdate +' '+crHour +':'+ crMinute +':'+ crSecond;
						}
					});
					self.set({'pos_sale_order_list' : orders});
				});
			});
		},
		addZero: function(value){
			if (value < 10) {
    			value = "0" + value;
    	    }
    	    return value;
    	},
		create_sale_order: function(delivery_done){
            var self = this;
            var order = this.get_order();
	        var currentOrderLines = order.get_orderlines();
	        var customer_id = order.get_client().id;
	        var location_id = self.config.stock_location_id ? self.config.stock_location_id[0] : false;
	        var paymentlines = false;
	        var paid = false;
	        var confirm = false;
            var orderLines = [];
            for(var i=0; i<currentOrderLines.length;i++){
                orderLines.push(currentOrderLines[i].export_as_JSON());
            }
            if(self.config.sale_order_operations === "paid" || order.get_order_id() || order.get_edit_quotation()) {
                paymentlines = [];
                _.each(order.get_paymentlines(), function(paymentline){
                    paymentlines.push({
                        'journal_id': paymentline.cashregister.journal_id[0],
                        'amount': paymentline.get_amount(),
                    })
                });
                paid = true
            }
            if(self.config.sale_order_operations === "confirm" && !order.get_edit_quotation()){
                confirm = true;
            }
            var vals = {
                orderlines: orderLines,
                customer_id: customer_id,
                location_id: location_id,
                journals: paymentlines,
                pricelist_id: order.pricelist.id || false,
                partner_shipping_id: order.get_shipping_address() || customer_id,
                partner_invoice_id: order.get_invoice_address() || customer_id,
                note: order.get_sale_note() || "",
                inv_id: order.get_inv_id() || false,
                order_date: order.get_sale_order_date() || false,
                requested_date: order.get_sale_order_requested_date() || false,
                sale_order_id: order.get_order_id() || false,
                edit_quotation: order.get_edit_quotation() || false,
                warehouse_id: self.config.warehouse_id ? self.config.warehouse_id[0] : false,
            }
            var params = {
				model: 'sale.order',
				method: 'create_sales_order',
				args: [vals, {'confirm': confirm, 'paid': paid,'delivery_done':delivery_done}],
			}
			rpc.query(params, {async: false}).then(function(sale_order){
                if(sale_order && sale_order[0]){
                    sale_order = sale_order[0];
                    if(paid && order.get_paying_sale_order()){
                        $('#btn_so').show();
                        if(sale_order){
                            order.set_sale_order_name(sale_order.name);
                        }
                        self.gui.show_screen('receipt');
                    } else{
                        var edit = order.get_edit_quotation();
                        order.finalize();
                        var url = window.location.origin + '/web#id=' + sale_order.id + '&view_type=form&model=sale.order';
                        self.gui.show_popup('saleOrder', {'url':url, 'name':sale_order.name, 'edit': edit});

                    }
                    var record_exist = false;
                    _.each(self.get('pos_sale_order_list'), function(existing_order){
                        if(existing_order.id === sale_order.id){
                            _.extend(existing_order, sale_order);
                            record_exist = true;
                        }
                    });
                    if (!record_exist){
                        var exist = _.findWhere(self.get('pos_sale_order_list'), {id: sale_order.id});
                        if(!exist){
                            var defined_orders = self.get('pos_sale_order_list');
                            var new_orders = [sale_order].concat(defined_orders);
                            self.db.add_sale_orders(new_orders);
                            new_orders.map(function(new_order){
                            	var dt = new Date(new Date(new_order.date_order) + "GMT");
    						   		var n = dt.toLocaleDateString();
	    						   	var crmon = self.addZero(dt.getMonth()+1);
							   	    var crdate = self.addZero(dt.getDate());
							   	    var cryear = dt.getFullYear();
							   	    var crHour = self.addZero(dt.getHours());
							   	    var crMinute = self.addZero(dt.getMinutes());
							   	    var crSecond = self.addZero(dt.getSeconds());
    						   	 new_order.date_order = cryear + '/' + crmon +'/'+ crdate +' '+crHour +':'+ crMinute +':'+ crSecond;
                            });
                            self.set({'pos_sale_order_list': new_orders})
                        }

                    }
                }
            }).fail(function(err, event){
                if(paid){
                    $('#btn_so').show();
                }
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                });
//                event.preventDefault();
            });
        },
	});

});