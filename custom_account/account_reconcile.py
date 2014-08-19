# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
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

from openerp.osv import fields, orm


class AccountMoveLineReconcileWriteoff(orm.TransientModel):
    _inherit = "account.move.line.reconcile.writeoff"

    def _get_date(self, cr, uid, context=None):
        date = None
        line_obj = self.pool.get('account.move.line')
        line_ids = context.get('active_ids')
        if line_ids:
            for line in line_obj.browse(cr, uid, line_ids, context=context):
                if date < line.date:
                    date = line.date
        return date
 
    _defaults = {
        'date_p': _get_date,
        #'journal_id': 54,
        #'writeoff_acc_id': 29274, 
        #'comment': 'frais',
    }


