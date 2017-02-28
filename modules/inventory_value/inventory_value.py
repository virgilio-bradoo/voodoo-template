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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import time

class InventoryValue(orm.Model):
    _name = "inventory.value"

    _columns = {
        'name': fields.char('name', char=64, required=True),
        'date': fields.date('Date', required=True),
        'inventory_line_ids': fields.one2many('inventory.value.line', 'inventory_id', 'Inventory Lines'),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'inventory.value', context=c),
    }

    def fill_inventory(self, cr, uid, ids, context=None):
        inventory = self.browse(cr, uid, ids, context=context)[0]
        if inventory.inventory_line_ids:
            raise orm.except_orm(_('Warning!'),_('The inventory already contains some lines'))
        product_obj = self.pool['product.product']
        product_ids = product_obj.search(cr, uid,
            [('procure_method', '=', 'make_to_stock'),
             ('supply_method', '=', 'buy'),
             ('sale_ok', '=', True)])
        inventory_line_vals = []
        for product in product_obj.browse(cr, uid, product_ids, context=context):
            if not product.qty_available > 0.0:
                continue
            line_vals = {
                'product_id': product.id,
                'immediatly_usable': product.immediately_usable_qty,
                'quantity': product.qty_available,
                'standard_price': product.standard_price,
                'supplier_id': product.seller_id and product.seller_id.id or False,
            }
            inventory_line_vals.append((0, 0,  line_vals))
        self.write(cr, uid, ids, {'inventory_line_ids': inventory_line_vals})
        return True

    def create_inventory_cron(self, cr, uid, context=None):
        date = time.strftime('%Y-%m-%d')
        name = 'Inventaire du ' + date
        inventory_id = self.create(
            cr, uid, {'name': name, 'date': date}, context=context)
        self.fill_inventory(cr, uid, [inventory_id], context=context)
        return True

    def inventory_print(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        datas = {
             'ids': ids,
             'model': 'inventory.value',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.value',
            'datas': datas,
            'nodestroy' : True
        }
        

class InventoryValueLine(orm.Model):
    _name = "inventory.value.line"

    _columns = {
        'inventory_id': fields.many2one('inventory.value', 'Inventory'),
        'product_id': fields.many2one('product.product', 'Product'),
        'default_code': fields.related('product_id', 'default_code', type='char', relation='product.product', string='Default Code'),
        'immediatly_usable': fields.float('Immediatly Usable'),
        'quantity': fields.float('Quantity'),
        'standard_price': fields.float('Standard price'),
        'supplier_id': fields.many2one('res.partner', 'Supplier'),
    }

