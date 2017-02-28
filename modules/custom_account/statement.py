# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP 
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.tools.translate import _
from openerp.osv import orm, fields
from openerp.addons.account_statement_base_completion.statement import ErrorTooManyPartner
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class AccountStatementCompletionRule(orm.Model):
    """Add a rule based on transaction ID"""
    _inherit = "account.statement.completion.rule"

    #Redifine the get function in order to return the good account
    def get_from_transaction_id_and_so(self, cr, uid, st_line, context=None):
        """
        Match the partner based on the transaction ID field of the SO.
        Then, call the generic st_line method to complete other values.
        In that case, we always fullfill the reference of the line with the SO name.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
            """
        st_obj = self.pool.get('account.bank.statement.line')
        res = {}

        so_obj = self.pool.get('sale.order')
        so_id = so_obj.search(cr, uid, [ 
            ('transaction_id', '=', st_line['transaction_id']),
            ], context=context)
        if len(so_id) > 1:
            #ATOS reuse the same transaction id, so if many have been found
            #we check the date to select the good one
            #Atos can be paid in 3x so we check the past month
            for delta in [60, 30, 0]:
                date = datetime.strptime(st_line['atos_payment_date'], DEFAULT_SERVER_DATE_FORMAT)
                min_date = date - timedelta(days=(delta+2))
                max_date = date - timedelta(days=(delta-2))
                min_date = datetime.strftime(min_date, DEFAULT_SERVER_DATE_FORMAT)
                max_date = datetime.strftime(max_date, DEFAULT_SERVER_DATE_FORMAT)
                so_id = so_obj.search(cr, uid, [ 
                    ('transaction_id', '=', st_line['transaction_id']),
                    ('date_order', '>', min_date),
                    ('date_order', '<=', max_date),
                    '|',
                        '&',
                            ('amount_total', '<=', 3.1*st_line['amount']),
                            ('amount_total', '>=', 2.9*st_line['amount']),
                        ('amount_total', '<=', 1.1*st_line['amount']),
                    ], context=context)
                print 'day transaction', delta, so_id
                if len(so_id) == 1:
                    break
        print so_id, st_line['transaction_id']
        if len(so_id) > 1:
            raise ErrorTooManyPartner(_('Line named "%s" (Ref:%s) was matched by more than '
                                        'one partner.') % (st_line['name'], st_line['ref']))
        if len(so_id) == 1:
            so = so_obj.browse(cr, uid, so_id[0], context=context)
            res['partner_id'] = so.partner_id.id
            res['ref'] = so.name
            st_vals = st_obj.get_values_for_line(cr,
                                                 uid,
                                                 profile_id=st_line['profile_id'],
                                                 master_account_id=st_line['master_account_id'],
                                                 partner_id=res.get('partner_id', False),
                                                 line_type=st_line['type'],
                                                 amount=st_line['amount'] if st_line['amount'] else 0.0,
                                                 context=context)
            res.update(st_vals)
        return res

    def get_from_email(self, cr, uid, st_line, context=None):
        """
        Match the partner based on the SO number and the reference of the statement
        line. Then, call the generic get_values_for_line method to complete other values.
        If more than one partner matched, raise the ErrorTooManyPartner error.

        :param int/long st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id': value,

            ...}
        """
        st_obj = self.pool.get('account.bank.statement.line')
        res = {}
        if st_line:
            partner_obj = self.pool.get('res.partner')
            email = st_line['name'].split(' ')[-1]
            partner_id = partner_obj.search(cr, uid, [
                ('email', '=', email),
                ('is_company', '=', True),
                ], context=context)
            if partner_id and len(partner_id) == 1:
                #TODO FIX ME in multi company mode
                account_id = 32226
                res = {
                    'partner_id': partner_id[0],
                    'account_id':account_id,
                }
            elif partner_id and len(partner_id) > 1:
                raise ErrorTooManyPartner(_('Line named "%s" (Ref:%s) was matched by more '
                                                'than one partner while looking on SO by ref.') %
                                              (st_line['name'], st_line['ref']))
        return res

class AccountStatementCompletionRule(orm.Model):
    _inherit = "account.statement.completion.rule"

    def get_functions(self, cr, uid, context=None):
        res = super(AccountStatementCompletionRule, self).get_functions(cr, uid, context=context)
        res.append(('get_from_email', 'From Email'))
        return res
