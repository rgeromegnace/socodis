odoo.define('aces_pos_enlarge_image.showimage', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var PopupWidget = require('point_of_sale.popups');

    screens.ProductListWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.model = options.model;
            this.productwidgets = [];
            this.weight = options.weight || 0;
            this.show_scale = options.show_scale || false;
            this.next_screen = options.next_screen || false;
            this.click_product_handler = function(e){
                var product = self.pos.db.get_product_by_id(this.dataset.productId);
                if($(e.target).attr('class') === "enlarge-image" || $(e.target).attr('class') === "fa fa-picture-o"){
                    self.gui.show_popup('show_image_popup',{'productnm':product.display_name,'product_id':this.dataset.productId});
                }else{
                    options.click_product_action(product);
                }
            };
            this.product_list = options.product_list || [];
            this.product_cache = new screens.DomCache();
        },
    });

    var ProductImagePopupWidget = PopupWidget.extend({
	    template: 'ProductImagePopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
            this.title = options['productnm']
            //var img = window.location.origin + '/web/image?model=product.product&field=image_medium&id='+options['product_id']
            var img = window.location.origin + '/web/image?model=product.product&field=image&id='+options['product_id']
            this.image_url = img;
	        this.renderElement();
	    },
	    click_confirm: function(){
	    	this.gui.close_popup();
	    },
	});

	gui.define_popup({name:'show_image_popup', widget: ProductImagePopupWidget});
});