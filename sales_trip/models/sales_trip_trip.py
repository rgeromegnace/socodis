# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from datetime import date
from datetime import time
from time import mktime

class Trip(models.Model):
    _name = "sales_trip.trip"
    _description="Sales Trip"
    name = fields.Char('Label', required=True)
    trip_day = fields.Date('Trip day')
    trip_day_week_number = fields.Integer(
        string='Trip day week number',
        compute='_compute_trip_day_week_number_',
        search='_search_trip_day_week_number_',
        store=False
    )

    commercial_id = fields.Many2one(
        'res.partner', string='Saler', required=True,
        domain=['&',('customer','=', False),('supplier', '=', False),('is_company', '=', False)]
    )

    customer_ids = fields.Many2many(
        'res.partner', string='Customers',
        domain=['&',('customer', '=', True),('is_company', '=', True)]
    )

    @api.depends('trip_day')
    def _compute_trip_day_week_number_(self):
        return self.trip_day.isocalendar(1)

    def _search_trip_day_week_number_(self, operator, value):
        current_year = self.get_today_year()
        next_week_number = value + 1

        # for more information about above code see:
        # - https://bit.ly/2kFUhTv
        # - https://bit.ly/2JASdnA
        # work only with python >=3.7
        # new_week_first_day = datetime.datetime.strptime(f"{current_year} {next_week_number} 1", '%G %V %u')
        # new_week_first_day = datetime.datetime.strptime("{0} {1} 1".format(current_year, next_week_number), '%G %V %u')

        # work with python <=3.6
        new_week_first_day = datetime.datetime.strptime(str(self.iso_to_gregorian(current_year, next_week_number, 1)), '%Y-%m-%d')
        # new_week_first_day = date.fromtimestamp(mktime(new_week_first_day))


        # convert the operator:
        # trip with week number > value have a trip day > new_week_first_day
        operator_map = {
            '>': '>', '>=': '>=', '<': '<', '<=': '<='
        }

        new_op = operator_map.get(operator, operator)
        return [('trip_day', new_op, new_week_first_day)]

    def get_dayname(self):
        """Return the french day name of trip day"""

        days = {1:"Lundi", 2:"Mardi", 3:"Mercredi", 4:"Jeudi", 5:"Vendredi", 6:"Samedi", 7:"Dimanche"}

        trip_day_as_date = fields.Date.from_string(self.trip_day)
        return days[trip_day_as_date.isoweekday()]


    def name_get(self):
        result = []
        for record in self:
            # result.append((record.id, f"TOURNEE DU {record.get_dayname()} de {record.commercial_id.name}"))
            result.append((record.id, "TOURNEE DU {0} de {1}".format(record.get_dayname(), record.commercial_id.name)))
        return result

    @api.model
    def get_commercial_next_week_trips(self, commercial_id):
        """Return all next week trips of the commercial passing in parameter"""

        trip = self.env['sales_trip.trip']
        domain = ['&',
                    ('trip_day_week_number','>=',self.get_today_week_number()),
                    ('commercial_id', '=', commercial_id)]

        return trip.search(domain)

    def get_today_week_number(self):
        """Return the today week number"""

        today = date.today()
        iso_result = today.isocalendar()
        return iso_result[1]

    def get_today_year(self):
        """Return the current year"""

        today = date.today()
        iso_result = today.isocalendar()
        return iso_result[0]

    def iso_year_start(self, iso_year):
        """The gregorian calendar date of the first day of the given ISO year"""
        fourth_jan = datetime.date(iso_year, 1, 4)
        delta = datetime.timedelta(fourth_jan.isoweekday()-1)
        return fourth_jan - delta

    def iso_to_gregorian(self, iso_year, iso_week, iso_day):
        """Gregorian calendar date for the given ISO year, week and day"""
        year_start = self.iso_year_start(iso_year)
        return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)

