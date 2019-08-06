# -*- coding: utf-8 -*-
{
    'name': "Sales trip",

    'summary': """
        Allow to manage sales trip""",

    'description': """
        Allow to manage sales trip
    """,

    'author': "Digitom",
    'website': "http://www.digitom.fr",
    'licence': "AGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '11.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/groups.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/sales_trip_menus.xml',
        'views/sales_trip_trip.xml',
        'views/sales_trip_trip_template.xml',
        'data/automatic_compute_trips.xml',
        'wizard/trip/sales_trip_trip_report_view.xml',
        'wizard/dialogs/sales_trip_dialog_view.xml',
        'reports/trip/sales_trip_trip_report.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}