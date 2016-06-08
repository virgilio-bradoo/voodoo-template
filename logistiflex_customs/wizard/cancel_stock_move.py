# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields


class CancelStockMove(osv.osv_memory):
    _name = "cancel.stock.move"

    _columns = {
        'comment': fields.text(
                string='Comment',
                readonly=True),
#        'move_id': fields.many2one('stock.move')
    }

    def cancel_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        move_id = context.get('active_id', False)
        if move_id:
            self.pool['stock.move'].action_cancel(
                    cr, uid, [move_id], context=context)
        return {'type': 'ir.actions.act_window_close'}
