odoo.define('aspl_pos_create_so_extension.screen', function (require) {
	"use strict";

	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var core = require('web.core');
	var models = require('point_of_sale.models');
	var rpc = require('web.rpc');

	var QWeb = core.qweb;
	var _t = core._t;

	var SaleOrderButton = screens.ActionButtonWidget.extend({
	    template: 'SaleOrderButton',
	    button_click: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        var currentOrderLines = order.get_orderlines();
	        var lines = [];
           _.each(currentOrderLines, function(line){
               if(line.product.invoice_policy == "delivery"){
               	lines.push(line)
               }
           })
	        if(currentOrderLines.length <= 0){
	            alert('No product selected !');
	        } else if(order.get_client() == null) {
	            alert('Please select customer !');
	        } else if (lines.length != 0){
	        	self.gui.show_popup('so_confirm_popup', {'sale_order_button': self,'deliver_products':lines});
	        } else{
	        	self.gui.show_popup('sale_order_popup', {'sale_order_button': self});
	        }
	    },
	});

	screens.define_action_button({
	    'name': 'saleorder',
	    'widget': SaleOrderButton,
	    'condition': function(){
	        return this.pos.config.sale_order_operations == "draft" || this.pos.config.sale_order_operations == "confirm" || this.pos.get_order().get_edit_quotation();
	    },
	});

	var ViewSaleOrdersButton = screens.ActionButtonWidget.extend({
	    template: 'ViewSaleOrdersButton',
	    button_click: function(){
            this.gui.show_screen('saleorderlist');
	    },
	});

	screens.define_action_button({
	    'name': 'viewsaleorder',
	    'widget': ViewSaleOrdersButton,
	});

	var EditQuotationButton = screens.ActionButtonWidget.extend({
	    template: 'EditQuotationButton',
	    button_click: function(){
            var self = this;
	        var order = this.pos.get_order();
	        var currentOrderLines = order.get_orderlines();
	        if(currentOrderLines.length <= 0){
	            alert('No product selected !');
	        } else if(order.get_client() == null) {
	            alert('Please select customer !');
	        } else {
	        	self.gui.show_popup('sale_order_popup', {'sale_order_button': self});
	        }
	    },
	});

	screens.define_action_button({
	    'name': 'EditQuotationButton',
	    'widget': EditQuotationButton,
	});

	screens.PaymentScreenWidget.include({
		renderElement: function() {
			var self = this;
	        this._super();
            this.$('#btn_so').click(function(){
            	var order = self.pos.get_order();
            	var lines = [];
                if(order){
                	var currentOrderLines = order.get_orderlines();
                	_.each(currentOrderLines, function(line){
                        if(line.product.invoice_policy == "delivery"){
                        	lines.push(line)
                        }
                    })
                	var paymentline_ids = [];
                    if(order.get_paymentlines().length > 0){
                        if(currentOrderLines.length <= 0){
                            alert('Empty order');
                        } else if(order.get_client() == null) {
                            alert('Please select customer !');
                        } else {
                            $('#btn_so').hide();
                            order.set_paying_sale_order(true);
                            if(!order.get_order_id() || order.get_edit_quotation()){
                            	if (lines.length != 0){
                    	        	self.gui.show_popup('so_confirm_popup', {'payment_obj': self,'deliver_products':lines});
                    	        } else{
                    	        	self.gui.show_popup('sale_order_popup', {'payment_obj': self});
                    	        }
//                                self.gui.show_popup('sale_order_popup', {'payment_obj': self});
                            } else {
                                self.pos.create_sale_order();
                            }
                        }
                    }
                }
            });
		},
		order_changes: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        var total = order ? order.get_total_with_tax() : 0;
	        if (!order) {
	            return;
	        } else if (order.is_paid()) {
	            self.$('.next').addClass('highlight');
	        } else if(order.get_due() == 0 || order.get_due() == total ){
	            self.$('#btn_so').removeClass('highlight');
	        } else {
	            self.$('.next').removeClass('highlight');
	            self.$('#btn_so').addClass('highlight');
	        }
	    },
	    click_set_customer: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        if(!order.get_sale_order_pay()){
	            self._super();
	        }
	    },
	    click_back: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        if(order.get_sale_order_pay()){
                this.gui.show_popup('confirm',{
                    title: _t('Discard Sale Order'),
                    body:  _t('Do you want to discard the payment of sale order '+ order.get_sale_order_name() +' ?'),
                    confirm: function() {
                        order.finalize();
                    },
                });
	        } else {
	            self._super();
	        }
	    },
	    validate_order: function(force_validation) {
	    	var self = this;
	    	var order = self.pos.get_order();
	    	if(order.get_sale_order_pay()){
	    		return
	    	} else{
	    		this._super(force_validation);
	    	}
	    },
	});

	/* Sale Order list screen */
	var SaleOrderListScreenWidget = screens.ScreenWidget.extend({
	    template: 'SaleOrderListScreenWidget',
	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        this.reload_btn = function(){
	        	$('.fa-refresh').toggleClass('rotate', 'rotate-reset');
	        	self.reloading_orders();
	        };
	    },
	    filter:"all",
        date: "all",
	    start: function(){
	    	var self = this;
            this._super();

            this.$('.back').click(function(){
                self.gui.back();
            });
            var orders = self.pos.get('pos_sale_order_list');
            this.render_list(orders);
            $('input#datepicker').datepicker({
           	    dateFormat: 'yy-mm-dd',
                autoclose: true,
                closeText: 'Clear',
                showButtonPanel: true,
                onSelect: function (dateText, inst) {
                	var date = $(this).val();
					if (date){
					    self.date = date;
					    self.render_list(orders);
					}
				},
				onClose: function(dateText, inst){
                    if( !dateText ){
                        self.date = "all";
                        self.render_list(orders);
                    }
                }
           }).focus(function(){
                var thisCalendar = $(this);
                $('.ui-datepicker-close').click(function() {
                    thisCalendar.val('');
                    self.date = "all";
                    self.render_list(orders);
                });
           });

          //button draft
            this.$('.button.draft').click(function(){
            	var orders=self.pos.get('pos_sale_order_list');
            	if(self.$(this).hasClass('selected')){
            		if(!self.pos.user.display_own_sales_order){
		        		self.$(this).removeClass('selected');
		        		$('.pay_button, .quotation_edit_button').show();
		        		self.filter = "all";
            		}
        		}else{
        			if(self.$('.button.paid').hasClass('selected')){
            			self.$('.button.paid').removeClass('selected');
            		}
        			if(self.$('.button.confirm').hasClass('selected')){
            			self.$('.button.confirm').removeClass('selected');
            		}
        			if(self.$('.button.my_orders').hasClass('selected')){
            			self.$('.button.my_orders').removeClass('selected');
            		}
            		$('.pay_button, .quotation_edit_button').show();
        			self.$(this).addClass('selected');
	        		self.filter = "draft";
        		}
        		self.render_list(orders);
            });

            //button paid
        	this.$('.button.paid').click(function(){
        		var orders=self.pos.get('pos_sale_order_list');
        		if(self.$(this).hasClass('selected')){
        			if(!self.pos.user.display_own_sales_order){
		        		self.$(this).removeClass('selected');
		        		$('.pay_button').show();
		        		$('.quotation_edit_button').show();
		        		self.filter = "all";
        			}
        		}else{
        			if(self.$('.button.draft').hasClass('selected')){
            			self.$('.button.draft').removeClass('selected');
            		}
        			if(self.$('.button.confirm').hasClass('selected')){
            			self.$('.button.confirm').removeClass('selected');
            		}
        			if(self.$('.button.my_orders').hasClass('selected')){
            			self.$('.button.my_orders').removeClass('selected');
            		}
        			self.$(this).addClass('selected');
        			$('.pay_button').hide();
        			$('.quotation_edit_button').hide();
	        		self.filter = "done";
        		}
        		self.render_list(orders);
            });
        	 //button confirm
            this.$('.button.confirm').click(function(){
            	var orders = self.pos.get('pos_sale_order_list');
            	if(self.$(this).hasClass('selected')){
            		if(!self.pos.user.display_own_sales_order){
		        		self.$(this).removeClass('selected');
		        	    $('.pay_button, .quotation_edit_button').show();
		        		self.filter = "all";
            		}
        		}else{
        			if(self.$('.button.paid').hasClass('selected')){
            			self.$('.button.paid').removeClass('selected');
            		}
        			if(self.$('.button.draft').hasClass('selected')){
            			self.$('.button.draft').removeClass('selected');
            		}
        			if(self.$('.button.my_orders').hasClass('selected')){
            			self.$('.button.my_orders').removeClass('selected');
            		}
            		$('.pay_button').show();
            		$('.quotation_edit_button').hide();
        			self.$(this).addClass('selected');
	        		self.filter = "sale";
        		}
        		self.render_list(orders);
            });

            this.$('.button.my_orders').click(function(){
        		var orders = self.pos.get('pos_sale_order_list');
            	if(self.$(this).hasClass('selected')){
            		if(!self.pos.user.display_own_sales_order){
		        		self.$(this).removeClass('selected');
		        	    $('.pay_button, .quotation_edit_button').show();
		        		self.filter = "all";
            		}
        		}else{
        			if(self.$('.button.paid').hasClass('selected')){
            			self.$('.button.paid').removeClass('selected');
            		}
        			if(self.$('.button.draft').hasClass('selected')){
            			self.$('.button.draft').removeClass('selected');
            		}
        			if(self.$('.button.confirm').hasClass('selected')){
            			self.$('.button.confirm').removeClass('selected');
            		}
            		$('.pay_button').show();
            		$('.quotation_edit_button').hide();
        			self.$(this).addClass('selected');
                	self.filter = "my_orders";
        		}
            	self.render_list(orders);
            });

          this.$('.sale-order-list-contents').delegate('#pay_amount','click',function(event){
            	var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_sale_order_by_id(order_id);
                if(result.state == "cancel"){
                	alert("Sorry, This order is cancelled");
                	return
                }
                if(result.state == "done"){
                	alert("Sorry, This Order is already locked");
                	return
                }

                var selectedOrder = self.pos.get_order();
                if (result && result.order_line.length > 0) {
                    var count = 0;
               	 	var currentOrderLines = selectedOrder.get_orderlines();
               	 	if(currentOrderLines.length > 0) {
	                 	selectedOrder.set_order_id('');
	                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
							_.each(currentOrderLines,function(item) {
								selectedOrder.remove_orderline(item);
							});
	                    }
               	 	}
                    var partner = null;
                    if (result.partner_id && result.partner_id[0]) {
                        var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    }
                    selectedOrder.set_client(partner);
               	 	selectedOrder.set_sale_order_name(result.name);
                    // Partial Payment
                    if(self.pos.config.paid_amount_product){
                        var paid_amount = 0.00;
                        var first_invoice = false;
                        if(result.invoice_ids.length > 0){
                        	var params = {
                 				model: 'account.invoice',
                 				method: 'search_read',
                 				domain: [['id', 'in', result.invoice_ids],['state', 'not in', ['paid']]]
                 			}
                 			rpc.query(params, {async: false}).then(function(invoices){
                                if(invoices){
                                    first_invoice = invoices[0];
                                    _.each(invoices, function(invoice){
                                    	paid_amount += invoice.amount_total - invoice.residual
                                    })
                                }
                            });
                            if(paid_amount){
                                var product = self.pos.db.get_product_by_id(self.pos.config.paid_amount_product[0]);
                                selectedOrder.add_product(product, {price: paid_amount, quantity: -1});
                            }
                            if (first_invoice){
                                selectedOrder.set_inv_id(first_invoice.id)
                            }
                        }
                    } else {
                    	self.gui.show_popup('error-traceback',{
							title: _t("Configuration Required"),
							body:  _t("Please configure dummy product for paid amount from POS configuration"),
						});
						return
                    }
                    // Partial Payment over
                    if (result.order_line) {
                    	var params = {
            				model: 'sale.order.line',
            				method: 'search_read',
            				domain: [['id', 'in', result.order_line]]
            			}
            			rpc.query(params, {async: false}).then(function(result_lines){
                            _.each(result_lines, function(res){
                                 count += 1;
                                 var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
                                 if(product){
                                     var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
                                     line.set_quantity(res.product_uom_qty);
                                     line.set_unit_price(res.price_unit)
                                     line.set_discount(res.discount)
                                     selectedOrder.add_orderline(line);
                                     selectedOrder.select_orderline(selectedOrder.get_last_orderline());
                                 }
                            });
                         });

                    }
                    selectedOrder.set_order_id(order_id);
					selectedOrder.set_sequence(result.name);
					selectedOrder.set_sale_order_pay(true);
					self.gui.show_screen('payment');
					self.pos.gui.screen_instances.payment.renderElement();
					$(self.pos.gui.screen_instances.payment.el).find('.button.next, .button.js_invoice').hide();
                }

            });

            this.$('.sale-order-list-contents').delegate('#edit_quotation','click',function(event){
                var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_sale_order_by_id(order_id);
                if(result.state == "cancel"){
                	alert("Sorry, This order is cancelled");
                	return
                }
                if(result.state == "done"){
                	alert("Sorry, This Order is already locked");
                	return
                }
                if(result.state == "sale"){
                	alert("Sorry, This Order is confirmed");
                	return
                }
                var selectedOrder = self.pos.get_order();
                if (result && result.order_line.length > 0) {
                    var count = 0;
               	 	var currentOrderLines = selectedOrder.get_orderlines();
               	 	if(currentOrderLines.length > 0) {
	                 	selectedOrder.set_order_id('');
	                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
							_.each(currentOrderLines,function(item) {
								selectedOrder.remove_orderline(item);
							});
	                    }
               	 	}
                    var partner = null;
                    if (result.partner_id && result.partner_id[0]) {
                        var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    }
                    selectedOrder.set_client(partner);
                    selectedOrder.set_shipping_address(result.partner_shipping_id ? result.partner_shipping_id[0] : 0)
                    selectedOrder.set_invoice_address(result.partner_invoice_id ? result.partner_invoice_id[0] : 0)
               	 	selectedOrder.set_sale_order_name(result.name);
               	 	selectedOrder.set_sale_order_date(result.date_order);
               	 	selectedOrder.set_sale_order_requested_date(result.requested_date);
               	 	var params = {
         				model: 'sale.order.line',
         				method: 'search_read',
         				domain: [['id', 'in', result.order_line]]
         			}
         			rpc.query(params, {async: false}).then(function(result_lines){
                        _.each(result_lines, function(res){
                             count += 1;
                             var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
                             if(product){
                                 var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
                                 line.set_quantity(res.product_uom_qty);
                                 line.set_unit_price(res.price_unit);
                                 line.set_discount(res.discount);
                                 selectedOrder.add_orderline(line);
                                 selectedOrder.select_orderline(selectedOrder.get_last_orderline());
                             }
                        });
                     });
               	}
                selectedOrder.set_order_id(order_id);
                selectedOrder.set_edit_quotation(true);
                selectedOrder.set_sequence(result.name);
                self.pos.gui.screen_instances.payment.renderElement();
                $(self.pos.gui.screen_instances.payment.el).find('.button.next, .button.js_invoice').hide();
                self.gui.show_screen('products');
            });

          //search box
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });

	    },
	    show: function(){
	        this._super();
	        this.reload_orders();
	        $('.button.my_orders').trigger('click');
	    },
	    perform_search: function(query, associate_result){
	        var self = this;
            if(query){
                var orders = this.pos.db.search_order(query);
                if ( associate_result && orders.length === 1){
                    this.gui.back();
                }
                this.render_list(orders);
            }else{
                var orders = self.pos.get('pos_sale_order_list');
                this.render_list(orders);
            }
        },
        clear_search: function(){
            var orders = this.pos.get('pos_sale_order_list');
            this.render_list(orders);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
	    render_list: function(orders){
        	var self = this;
            var contents = this.$el[0].querySelector('.sale-order-list-contents');
            contents.innerHTML = "";
            var temp = [];
            if(self.filter !== "" && self.filter !== "all" && self.filter != "my_orders"){
	            orders = $.grep(orders,function(order){
	            	return order.state === self.filter;
	            });
            }
            if(self.date !== "" && self.date !== "all"){
            	var x = [];
            	for (var i=0; i<orders.length;i++){
                    var date_order = $.datepicker.formatDate("yy-mm-dd",new Date(orders[i].date_order));
            		if(self.date === date_order){
            			x.push(orders[i]);
            		}
            	}
            	orders = x;
            }
            if(self.filter == 'my_orders'){
            	var user_id = '';
    			if(self.pos.get_cashier()){
    				if(self.pos.get_cashier()){
            			user_id = self.pos.get_cashier().id;
            		}
    			}else{
    				if(self.pos.user){
                		user_id = self.pos.user.id;
                	}
    			}
            	if(user_id && orders.length > 0){
            		var user_orders = [];
            		orders = $.grep(orders,function(order){
    	            	return order.user_id[0] === user_id;
    	            });
            	}
            }
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                var order    = orders[i];
                order.amount_total = parseFloat(order.amount_total).toFixed(2);
            	var clientline_html = QWeb.render('SaleOrderlistLine',{widget: this, order:order});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
            $("table.sale-order-list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage:Number(self.pos.config.sale_order_record_per_page) > 0 ? Number(self.pos.config.sale_order_record_per_page) : 10
			});
        },
        reload_orders: function(){
        	var self = this;
            var orders=self.pos.get('pos_sale_order_list');
            this.render_list(orders);
        },
	    reloading_orders: function(){
	    	var self = this;
	    	var params = {
				model: 'sale.order',
				method: 'search_read',
				domain: self.pos.domain_sale_order
			}
			rpc.query(params, {async: false}).then(function(result){
	    		self.pos.db.add_sale_orders(result);
	    		if(self.pos.user.display_own_sales_order){
		    		var user_orders = [];
		    		result.map(function(sale_order){
						if(sale_order.user_id[0] == self.pos.user.id){
							user_orders.push(sale_order);
						}
					});
		    		result = user_orders;
	    		}
	    		result.map(function(data){
	    			var dt = new Date(new Date(data.date_order) + "GMT");
				   	var n = dt.toLocaleDateString(); 
				   	var crmon = self.pos.addZero(dt.getMonth()+1);
			   	    var crdate = self.pos.addZero(dt.getDate());
			   	    var cryear = dt.getFullYear();
			   	    var crHour = self.pos.addZero(dt.getHours());
			   	    var crMinute = self.pos.addZero(dt.getMinutes());
			   	    var crSecond = self.pos.addZero(dt.getSeconds());
				   	 data.date_order = cryear + '/' + crmon +'/'+ crdate +' '+crHour +':'+ crMinute +':'+ crSecond;
	    		});
	    		self.pos.set({'pos_sale_order_list' : result});
	    		self.reload_orders();
	    		return self.pos.get('pos_sale_order_list');
	    	}).fail(function (error, event){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
              	self.gui.show_popup('error-traceback',{
                      message: error.data.message,
                      comment: error.data.debug
                  });
                }
              // prevent an error popup creation by the rpc failure
              // we want the failure to be silent as we send the orders in the background
              event.preventDefault();
              console.error('Failed to send orders:', orders);
              var orders=self.pos.get('pos_sale_order_list');
      	          self.reload_orders();
      	          return orders
              });
	    },
	    renderElement: function(){
	    	var self = this;
	    	self._super();
	    	self.el.querySelector('.button.reload').addEventListener('click',this.reload_btn);
	    },
	});
	gui.define_screen({name:'saleorderlist', widget: SaleOrderListScreenWidget});

});