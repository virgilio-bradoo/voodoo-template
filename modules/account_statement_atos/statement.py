# -*- coding: utf-8 -*-
###############################################################################
#
#   account_statement_bnp_import for OpenERP
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>
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

from openerp.osv import orm, fields
from tools.translate import _

class AccountStatementProfil(orm.Model):
    _inherit = "account.statement.profile"

    def get_import_type_selection(self, cr, uid, context=None):
        """
        Has to be inherited to add parser
        """
        res = super(AccountStatementProfil, self).get_import_type_selection(cr, uid, context=context)
        res.extend([
            ('atos_csvparser', 'Parser for Atos import statement'),
        ])
        return res


    def _add_special_line(self, cursor, uid, statement_id, parser, result_row_list, profile, context=None):
        super(AccountStatementProfil, self)._add_special_line(cursor, uid, statement_id, parser, result_row_list, profile, context=context)
      	if parser.parser_for('atos_csvparser') and parser.get_refund_amount():
            partner_id = profile.partner_id and profile.partner_id.id or False
            transfer_account_id = profile.internal_account_transfer_id.id or False
            statement_line_obj = self.pool.get('account.bank.statement.line')
            date = parser.get_statement_date()
            period_id = self._get_period(cursor, uid, date, context=context)
            transfer_vals = {
                'name': _('Transfer'),
                'date': parser.get_statement_date(),
                'period_id': period_id,
                'amount': parser.get_refund_amount(),
                'partner_id': partner_id,
                'type': 'general',
                'statement_id': statement_id,
                'account_id': transfer_account_id,
                'ref': 'transfer',
                # !! We set the already_completed so auto-completion will not update those values !
                'already_completed': True,
            }

            statement_line_obj.create(cursor, uid, transfer_vals, context=context)



class AccountBankStatetementLine(orm.Model):
    _inherit = 'account.bank.statement.line'

    _columns = {
        'atos_payment_sequence': fields.integer('Payment Sequence'),
        'atos_payment_date': fields.date('Orignal Payment Date'),
    }    

