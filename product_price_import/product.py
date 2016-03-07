# -*- coding: utf-8 -*-
###############################################################################
#
#   account_statement_be2bill for OpenERP
#   Copyright (C) 2014-TODAY Akretion <http://www.akretion.com>.
#   @author Florian da Costa <florian.dacosta@akretion.com>
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

class MrpBom(orm.Model):
    _inherit = "mrp.bom"

    def get_parent_from_component(self, cr, uid, ids, context=None):
        parent_ids = []
        for component in self.browse(cr, uid, ids, context=context):
            parent = component.bom_id or False
            while parent:
                parent_ids.append(component.bom_id.id)
                parent = parent.bom_id or False
        return parent_ids

    def update_product_bom_price(self, cr, uid, ids, fields, context=None):
        product_obj = self.pool['product.product']
        for bom in self.browse(cr, uid, ids, context=context):
            vals = {i: 0.0 for i in fields}
            for line in bom.bom_lines:
                for key in fields:
                    vals[key] += getattr(line.product_id, key) * line.product_qty
            context['bom_updated'] = True
            product_obj.write(cr, uid, [bom.product_id.id], vals, context=context)
        return True

class ProductProduct(orm.Model):
    _inherit = "product.product"

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        super(ProductProduct, self).write(cr, uid, ids, vals, context=context)
        price_fields = ['list_price', 'list_price_tax_inc']
        fields_to_update = list(set(price_fields).intersection(vals.keys()))
        if fields_to_update and not context.get('bom_updated', False):
            bom_obj = self.pool['mrp.bom']
            for product in self.browse(cr, uid, ids, context=context):
                component_ids = bom_obj.search(cr, uid,
                    [('product_id', '=', product.id), ('bom_lines', '=', False)])
                parent_bom_ids = bom_obj.get_parent_from_component(
                                    cr, uid, component_ids, context=context)
                prods = []
                no_prods = []
                for bom in bom_obj.browse(cr, uid, parent_bom_ids):
                    if bom.product_id.prestashop_bind_ids or bom.product_id.prestashop_combinations_bind_ids:
                        prods.append(bom.product_id.id)
                    else:
                        no_prods.append(bom.product_id.id)
                #product_parent_bom_ids = [bom.product_id.id for bom in bom_obj.browse(cr, uid, product_parent_bom_ids, context=context)]
                bom_obj.update_product_bom_price(cr, uid, parent_bom_ids, fields_to_update, context=context)
        return True

