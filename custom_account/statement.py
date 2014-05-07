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
            if so.payment_method_id.account_id:
                print 'acount name', so.payment_method_id.account_id.name
                res['account_id'] = so.payment_method_id.account_id.id
        return res

    # OVERWRITE get_ref and so in order to pass the account
    #we should refactor teh abse method in order to allow this king of overwrite
    #without redifinition
    def get_from_ref_and_so(self, cr, uid, st_line, context=None):
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
            so_obj = self.pool.get('sale.order')
            so_id = so_obj.search(cr,
                                  uid,
                                  [('name', '=', st_line['ref'])],
                                  context=context)
            if so_id:
                if so_id and len(so_id) == 1:
                    so = so_obj.browse(cr, uid, so_id[0], context=context)
                    res['partner_id'] = so.partner_id.id
                elif so_id and len(so_id) > 1:
                    raise ErrorTooManyPartner(_('Line named "%s" (Ref:%s) was matched by more '
                                                'than one partner while looking on SO by ref.') %
                                              (st_line['name'], st_line['ref']))
        ###END COPY/PASTE
                so = so_obj.browse(cr, uid, so_id[0], context=context)
                if so.payment_method_id.account_id:
                    print 'acount name', so.payment_method_id.account_id.name
                    res['account_id'] = so.payment_method_id.account_id.id
        return res




#class AccountBankStatement(orm.Model):
#    _inherit = "account.bank.statement"
#
#    def button_confirm_bank(self, cr, uid, ids, context=None):
#        stat_line_obj = self.pool['account.bank.statement.line']
#        for stat in self.browse(cr, uid, ids, context=context):
#            transfers_amount = 0
#            transfers_refund_amount = 0
#            main_transfer_line = None
#            main_refund_transfer_line = None
#            if stat_line_obj.search(cr, uid, [('account_id', '=', 27930), ('statement_id', '=', stat.id)], context=context):
#                if stat_line_obj.search(cr, uid, [('account_id', '=', 28309), ('statement_id', '=', stat.id)], context=context):
#                    print "REMOVE 3x transfers!"
#                    for line in stat.line_ids:
#                        if line.account_id.id == 28309:
#                            line.unlink()
#                        elif line.account_id.id == 28061:
#                            if line.amount < 0:
#                                main_transfer_line = line 
#                            else:
#                                main_refund_transfer_line = line
#                        else:
#                            if line.amount > 0:
#                                transfers_amount += line.amount
#                            else:
#                                transfers_refund_amount += line.amount
#                    main_transfer_line.write({'amount': - transfers_amount})
#                    if transfers_refund_amount:
#                        main_refund_transfer_line.write({'amount': - transfers_refund_amount})
#        return super(AccountBankStatement, self).button_confirm_bank(cr, uid, ids, context=context)
#
