# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2011-2014 Akretion (http://www.akretion.com).
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


from openerp.osv import orm
from openerp.tools.translate import _
LOGISTIFLEX_ADDRESS_ID = 42861
IP_BOX = '192.168.0.32'

class StockPickingAbstract():

    def print_label(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Process only one a single id at a time.'
        label_obj = self.pool['shipping.label']
        label_ids = label_obj.search(cr, uid, [
            ['res_id', 'in', ids],
            ], context=context)
        action_list = []
        for label in label_obj.browse(cr, uid, label_ids, context=context):
            action_list.append({
                'url' : 'http://%s:8069/cups/printData' % IP_BOX,
                'params': {
                    'args': ['zebra', label.datas],
                    'kwargs': {'options': {'raw': True}},
                    }
                })
        return {
            'type': 'ir.actions.act_proxy',
            'action_list': action_list,
            }


    def _get_label_sender_address(self, cr, uid, picking, context=None):
        partner_obj = self.pool['res.partner']
        return partner_obj.browse(
            cr, uid, LOGISTIFLEX_ADDRESS_ID, context=context)


class stock_split_into(orm.TransientModel):
    _inherit = "stock.split.into"
    _description = "Split into"
 
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        context.update({
            'form_view_ref': None,
            'tree_view_ref': None,
            })
        return super(stock_split_into, self).fields_view_get(
            cr, user, view_id=None, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
