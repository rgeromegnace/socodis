# -*- coding: utf-8 -*-
#################################################################################
# Author      : Digitom (<www.digitom.fr>)
# Copyright(c): 2018-Present Digitom
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': "Digitom",
    'summary': "Module spécifique à KYLIANE IMPORT",
    'description': """Module spécifique à KYLIANE IMPORT""",
    'author': "DIGITOM",
    'licence': "AGPL-3",
    'website': "http://www.digitom.fr",
    'category': "Uncategorized",
    'version': '11.0.1.1.1',
    'depends': ['base','sale','point_of_sale','account','web'],
    'data': [
        'security/groups.xml',
        'views/pos_config_views.xml',
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
        'views/stock_picking_view.xml',
        'views/res_company_view.xml',
        'views/report_invoice.xml',
        'views/tpimport_external_layout_standard.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/contact_views.xml',
        'wizard/stock_picking_confirm.xml',
        'security/ir.model.access.csv',
    ],
}