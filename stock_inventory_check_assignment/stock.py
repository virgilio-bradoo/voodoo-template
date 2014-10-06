# -*- coding: utf-8 -*-
################################################################################
#                                                                              #
#   multi_company_supplier for OpenERP                                         #
#   Copyright (C) 2014 Akretion Florian da Costa <florian.dacosta@akretion.com>#
#                                                                              #
#   This program is free software: you can redistribute it and/or modify       #
#   it under the terms of the GNU Affero General Public License as             #
#   published by the Free Software Foundation, either version 3 of the         #
#   License, or (at your option) any later version.                            #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#   GNU Affero General Public License for more details.                        #
#                                                                              #
#   You should have received a copy of the GNU Affero General Public License   #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################
from openerp.osv.orm import Model


class StockInventory(Model):
    _inherit = "stock.inventory"


    def action_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        location_obj = self.pool['stock.location']
        move_obj = self.pool['stock.move']
        prod_obj = self.pool['product.product']
        for inv in self.browse(cr, uid, ids, context=context):
            for line in inv.inventory_line_id:
                context.update({'location':[line.location_id.id]})
                pid = line.product_id.id
                amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], context=context)[pid]
                change = line.product_qty - amount

                if change and change < 0:
    
                    context.update({'states':('assigned',)})
                    context.update({'what':'out'})
                    qty_reserved = prod_obj.get_product_available(cr, uid, [pid], context=context)[pid]
                    qty_available = amount + qty_reserved + change
                    print "*****", qty_available, "kk", qty_reserved, "pp", change
                    if qty_available < 0:
                        missing_qty = -qty_available
                        move_ids = move_obj.search(
                                    cr, uid,
                                    [('location_id', '=', line.location_id.id),
                                     ('state', '=', 'assigned')],
                                    order='date_expected', context=context)
                        move_ids = move_ids[::-1]
                        for move in move_obj.browse(cr, uid, move_ids,
                                                    context=context):
                            if missing_qty > 0:
                                move_obj.cancel_assign(cr, uid, [move.id],
                                                       context=context)
                                missing_qty -= move.product_qty
                            else:
                                break
            
        return super(StockInventory, self).action_confirm(
                                                cr, uid, ids, 
                                                context=context)
