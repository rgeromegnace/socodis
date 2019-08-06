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
{
    'name': 'POS Enlarge Image',
    'category': 'Point of Sale',
    'summary': 'This module allows user to see large product image.',
    'description': """
User needs to select product from product list then Double click on order item and
it will display product name on title and product image in popup window.
""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 10, 
    'currency': 'EUR',
    'version': '1.0.1',
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/main_screenshot.png'],
    "data": [
        'views/point_of_sale.xml',
        'views/aces_pos_enlarge_image.xml'
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
