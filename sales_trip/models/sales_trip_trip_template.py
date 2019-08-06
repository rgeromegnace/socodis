# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from datetime import date
import time
from time import mktime

import logging

_logger = logging.getLogger(__name__)

class TripTemplate(models.Model):
    _name = 'sales_trip.trip_template'
    _description = 'Sales Trip Template'
    name = fields.Char('Label', required='True')

    TRIP_DAY_SELECTIONS = \
        [(1, 'Lundi'),
         (2, 'Mardi'),
         (3, 'Mercredi'),
         (4, 'Jeudi'),
         (5, 'Vendredi')]

    trip_day = fields.Selection(TRIP_DAY_SELECTIONS, 'Trip day', required=True)

    commercial_id = fields.Many2one(
        'res.partner', string='Saler', required=True,
        domain=[('partner_share','=', False)]
    )

    customer_ids = fields.Many2many(
        'res.partner', string='Customers',
        domain=['&',('customer', '=', True),('is_company', '=', True)]
    )

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         #result.append((record.id, f"TOURNEE DU  {record.name}-{record.create_date}"))
    #         result.append((record.id, f"{record.name}-{record.create_date}"))
    #     return result

    def get_trip_day_weekday(self):
        """Return the weekday number associated with the trip template trip day"""

        days = {"Lundi":1, "Mardi":2, "Mercredi":3, "Jeudi":4, "Vendredi":5, "Samedi":6, "Dimanche":7}

        return days[dict(self.TRIP_DAY_SELECTIONS)[self.trip_day]]

    @api.model
    def get_commercial_next_week_trips(self):
        """Return all next week trips of the commercial passing in parameter"""

        trips = self.env['sales_trip.trip']
        domain = ['&',
                    ('trip_day_week_number','>',self.get_today_week_number()),
                    ('commercial_id', '=', self.commercial_id.id)]

        return trips.search(domain)

    @api.model
    def get_commercial_trips_by_week_number(self, week_number):
        """Return all week trips associated with the week_number passing in parameter"""

        trips = self.env['sales_trip.trip']
        domain = ['&',
                    ('trip_day_week_number','=', week_number),
                    ('commercial_id', '=', self.commercial_id.id)]

        return trips.search(domain)

    @api.model
    def get_commercial_trip_templates(self):
        """Return all commercial trip template"""

        trip_templates = self.env['sales_trip.trip_template']
        domain = [('commercial_id', '=', self.commercial_id.id)]

        return trip_templates.search(domain)

    def compute_tripday(self, current_year, next_week_number, weekday):
        """Create the tripday date according to current year and week day"""

        # work only with python >=3.7
        #tripday = time.strptime(f"{current_year} {next_week_number} {weekday}", '%G %V %u')
        #tripday = time.strptime("{0} {1} {2}".format(current_year, next_week_number, weekday), '%G %V %u')

        # work with python <=3.6
        tripday = time.strptime(str(self.iso_to_gregorian(current_year, next_week_number, weekday)), '%Y-%m-%d')

        tripday = date.fromtimestamp(mktime(tripday))

        return tripday

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


    @api.multi
    def compute_trips(self):
        """Generate trips for the selected commercial"""
        _logger.info(TripTemplate.compute_trips.__name__)
        for trip_template in self:
            commercial_trips = trip_template.get_commercial_next_week_trips()

            # we delete commercial next week if exist
            if commercial_trips:
                commercial_trips.unlink()

            # we get all the commercial trip_template
            commercial_trip_templates = self.get_commercial_trip_templates()

            for commercial_trip_template in commercial_trip_templates:
                trip_template_weekday = commercial_trip_template.get_trip_day_weekday()
                current_year = commercial_trip_template.get_today_year()
                next_week_number = commercial_trip_template.get_today_week_number() + 1
                weekday = commercial_trip_template.get_trip_day_weekday()

                trip_day = commercial_trip_template.compute_tripday(current_year, next_week_number, weekday)

                customers_ids = [customer.id for customer in commercial_trip_template.customer_ids]
                # we create new next week trips
                trip_map = {
                    #'name': f"TOURNEE DU {trip_day} de {commercial_trip_template.commercial_id.name}",
                    'name': "TOURNEE DU {0} de {1}".format(trip_day, commercial_trip_template.commercial_id.name),
                    'trip_day': trip_day,
                    'commercial_id': commercial_trip_template.commercial_id.id,
                    'customer_ids': [(6, False, customers_ids)]
                    #'customer_ids': [(6, False, [120,263])]
                }

                record = self.env['sales_trip.trip'].create(trip_map)

    @api.model
    def compute_trips_cron(self):
        """Generate trips for the selected commercial"""
        #TODO: the method is called by the action cron but failed
        _logger.info(TripTemplate.compute_trips_cron.__name__)
        trip_template = self
        commercial_trips = trip_template.get_commercial_next_week_trips()

        # we delete commercial next week if exist
        if commercial_trips:
            commercial_trips.unlink()

        # we get all the commercial trip_template
        commercial_trip_templates = self.get_commercial_trip_templates()

        for commercial_trip_template in commercial_trip_templates:
            trip_template_weekday = commercial_trip_template.get_trip_day_weekday()
            current_year = commercial_trip_template.get_today_year()
            next_week_number = commercial_trip_template.get_today_week_number() + 1
            weekday = commercial_trip_template.get_trip_day_weekday()

            trip_day = commercial_trip_template.compute_tripday(current_year, next_week_number, weekday)

            customers_ids = [customer.id for customer in commercial_trip_template.customer_ids]
            # we create new next week trips
            trip_map = {
                #'name': f"TOURNEE DU {trip_day} de {commercial_trip_template.commercial_id.name}",
                'name': "TOURNEE DU {0} de {1}".format(trip_day, commercial_trip_template.commercial_id.name),
                'trip_day': trip_day,
                'commercial_id': commercial_trip_template.commercial_id.id,
                'customer_ids': [(6, False, customers_ids)]
                #'customer_ids': [(6, False, [120,263])]
            }

            record = self.env['sales_trip.trip'].create(trip_map)

    def iso_year_start(self, iso_year):
        """The gregorian calendar date of the first day of the given ISO year"""
        fourth_jan = datetime.date(iso_year, 1, 4)
        delta = datetime.timedelta(fourth_jan.isoweekday() - 1)
        return fourth_jan - delta

    def iso_to_gregorian(self, iso_year, iso_week, iso_day):
        """Gregorian calendar date for the given ISO year, week and day"""
        year_start = self.iso_year_start(iso_year)
        return year_start + datetime.timedelta(days=iso_day - 1, weeks=iso_week - 1)

