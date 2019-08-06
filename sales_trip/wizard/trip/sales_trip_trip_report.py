# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang, format_date
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TripReportWizard(models.TransientModel):

    _name = 'sales_trip.trip.report.wizard'

    commercial_ids = fields.Many2many(
        'res.partner', string='Salers',
        domain=[('partner_share', '=', False)],
        required = True
    )

    customer_ids = fields.Many2many(
        'res.partner', string='Customers',
        domain=['&',('customer', '=', True),('is_company', '=', True)]
    )

    see_non_endebted_customers = fields.Boolean(string='See non endebted customers also', default=False)

    customer_payment_term_ids = fields.Many2many('account.payment.term', string='Payment terms')

    trip_day = fields.Date(string="Trip date", required = True)

    @api.multi
    def get_report(self):
        """Call when button Get Report is click"""
        commercial_ids = self.commercial_ids
        trip_day = self.trip_day
        payment_terms = self.customer_payment_term_ids
        see_non_endebted_customers = self.see_non_endebted_customers

        if len(payment_terms) > 0:
            domain = ['&',
                      ('commercial_id','in', [id.id for id in commercial_ids]),
                      ('trip_day', '=', trip_day),
                      ('customer_ids.property_payment_term_id.id', 'in', [id.id for id in payment_terms])

            ]
        else:
            domain = ['&',('commercial_id', 'in', [id.id for id in commercial_ids]),('trip_day', '=', trip_day)]


        trips = self.env['sales_trip.trip'].search(domain)

        if len(trips) == 0:
            return self.display_dialog()
        else:
            data = {
                'ids': self.ids,
                'model': self._name,
                'form': {
                    'commercial_ids': [id.id for id in commercial_ids],
                    'trip_day': trip_day,
                    'payment_term_ids': [id.id for id in payment_terms] if len(payment_terms) > 0 else None,
                    'see_non_endebted_customers': see_non_endebted_customers
                },
                'trips': trips.ids
            }

            return self.env.ref('sales_trip.trip_report').report_action(self, data=data)

    @api.model
    def display_dialog(self):
        """Display the dialog message"""
        message = _('There is not trip that match your query.')
        params = {
            'title': _('No matched trips'),
            'message': message
        }
        view_id = self.env['sales_trip.dialog.wizard']
        new = view_id.create(params)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Warning'),
            'res_model': 'sales_trip.dialog.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': new.id,
            'view_id': self.env.ref('sales_trip.sales_trip_dialog_view', False).id,
            'target': 'new',
        }


class TripReport(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`."""

    _name = 'report.sales_trip.trip_report_view'

    options = {
        'all_entries': None,
        'analytic': None,
        'cash_basis': None,
        'comparison': None,
        'date': {
            'date': None,
            'filter': None,     # ex 'today'
            'string': None      #ex: 'As of 10/16/2018'
        },
        'hierarchy': None,
        'journals': None,
        'unfold_all': False,
        'unfolded_lines': []
    }

    def set_context(self, options):
        """This method will set information inside the context based on the options dict as some options need to be in context for the query_get method defined in account_move_line"""
        ctx = self.env.context.copy()
        if options.get('date') and options['date'].get('date_from'):
            ctx['date_from'] = options['date']['date_from']
        if options.get('date'):
            ctx['date_to'] = options['date'].get('date_to') or options['date'].get('date')
        if options.get('all_entries') is not None:
            ctx['state'] = options.get('all_entries') and 'all' or 'posted'
        if options.get('journals'):
            ctx['journal_ids'] = [j.get('id') for j in options.get('journals') if j.get('selected')]
        ctx['account_type'] = 'receivable'
        ctx['aged_balance'] = None

        return ctx

    def format_value(self, value, currency=False):
        if self.env.context.get('no_format'):
            return value
        currency_id = currency or self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        return res

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)

        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], []

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
                values['property_payment_term_id'] = browsed_partner.property_payment_term_id.id
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['property_payment_term_id'] = False

            if at_least_one_amount or self._context.get('include_nullified_amount'):
                res.append(values)

        return res, total, lines

    @api.model
    def get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        #results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        results, total, amls = self.with_context(
            include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted',
                                                                   30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                'columns_without_format': [{'name': sign * v} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'property_payment_term_id': values['property_payment_term_id']
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                        'columns_without_format': [{'name': v} for v in
                                    [line['period'] == 6 - i and (sign * line['amount']) or '' for i in
                                     range(7)]],
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'class': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'parent_id': 'partner_%s' % (values['partner_id'],),
                    'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    'columns_without_format': [{'name': sign * v} for v in
                                [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'],
                                 values['total']]],
                }
                lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 'None',
                'columns': [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                'columns_without_format': [{'name': sign * v} for v in
                            [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines

    @api.model
    def get_report_values(self, docids, data=None):
        commercial_ids = data['form']['commercial_ids']
        payment_term_ids = data['form']['payment_term_ids']
        trip_day = data['form']['trip_day']
        see_non_endebted_customers = data['form']['see_non_endebted_customers']
        trips = data['trips']

        commercial_records = self.env['res.partner'].browse([id for id in commercial_ids])

        docs = None
        commercials = []
        count = 0;

        trips = self.env['sales_trip.trip'].browse(trips)

        #we retreive all partners aged lines if any
        self.options['date']['date'] = trip_day
        aged_partner_lines = self.with_context(self.set_context(self.options)).get_lines(self.options)

        for commercial in commercial_records: # we browse all the commercial
            commercials.append([{'commercial_name': commercial.name}])
            total_customers_debt = 0.00
            for trip in trips.search(['&',
                ('commercial_id', '=', commercial.id),('trip_day', '=', trip_day)]): # we browse the commercial trip
                docs = []
                for customer_id in trip.customer_ids:
                    #we retreive the aged partner line
                    if payment_term_ids is not None:
                        aged_customer_line = [
                            line for line in aged_partner_lines
                                if line['id'] == 'partner_%s' % (customer_id.id)
                                   and line['property_payment_term_id'] in payment_term_ids
                        ]
                    else:
                        aged_customer_line = [
                            line for line in aged_partner_lines
                                if line['id'] == 'partner_%s' % (customer_id.id)
                        ]

                    if len(aged_customer_line) > 0:
                        docs.append({
                            'customer_name': customer_id.name,
                            'customer_payment_term': customer_id.property_payment_term_id.name,
                            'customer_city': customer_id.city,
                            'direction': aged_customer_line[0]['columns'][0]['name'],
                            '0-30': aged_customer_line[0]['columns'][1]['name'],
                            '30-60': aged_customer_line[0]['columns'][2]['name'],
                            '60-90': aged_customer_line[0]['columns'][3]['name'],
                            '90-120': aged_customer_line[0]['columns'][4]['name'],
                            '+120': aged_customer_line[0]['columns'][5]['name'],
                            'total': aged_customer_line[0]['columns'][6]['name'],
                        })
                        total_customers_debt += aged_customer_line[0]['columns_without_format'][6]['name']
                    elif see_non_endebted_customers == True:
                        if payment_term_ids is not None:
                            if customer_id.property_payment_term_id.id in payment_term_ids:
                                docs.append({
                                    'customer_name': customer_id.name,
                                    'customer_payment_term': customer_id.property_payment_term_id.name,
                                    'customer_city': customer_id.city,
                                    'direction': '0 €',
                                    '0-30': '0 €',
                                    '30-60': '0 €',
                                    '60-90': '0 €',
                                    '90-120': '0 €',
                                    '+120': '0 €',
                                    'total': '0 €',
                                })
                        else:
                            docs.append({
                                'customer_name': customer_id.name,
                                'customer_payment_term': customer_id.property_payment_term_id.name,
                                'customer_city': customer_id.city,
                                'direction': '0 €',
                                '0-30': '0 €',
                                '30-60': '0 €',
                                '60-90': '0 €',
                                '90-120': '0 €',
                                '+120': '0 €',
                                'total': '0 €',
                            })
            if docs != None and len(docs) > 0:
                commercials[count].extend([{'docs': docs}])
                commercials[count].extend([{'total_customers_debt': round(total_customers_debt, 2)}])
                count = count + 1
            else:
                commercials[count].extend([{'docs': []}])
                commercials[count].extend([{'total_customers_debt': 0}])
                count = count + 1


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'trip_day': trip_day,
            'commercials': commercials,
        }

