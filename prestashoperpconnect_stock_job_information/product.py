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

from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.product import ProductInventoryExport  
from openerp.addons.prestashoperpconnect.product_combination import CombinationInventoryExport 
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
from openerp.osv import fields, orm
from openerp.tools.translate import _



@prestashop(replacing=ProductInventoryExport)
class JobInfoProductInventoryExport(ProductInventoryExport):
    _model_name = ['prestashop.product.product']

    def _get_quantity(self, ori_filters):
        filters = ori_filters.copy()
        filters['display'] = '[quantity]'

        adapter = self.get_connector_unit_for_model(
            GenericAdapter, '_import_stock_available'
        )
 
        quantities = adapter.get(filters)
        all_qty = 0
        if not quantities['stock_availables']:
            return 'empty'
        quantities = quantities['stock_availables']['stock_available']
        if isinstance(quantities, dict):
            quantities = [quantities]
        for quantity in quantities:
            all_qty += int(quantity['quantity'])
        return all_qty

    def run(self, binding_id, fields):
        """ Export the product inventory to Prestashop """
        product = self.session.browse(self.model._name, binding_id)
        adapter = self.get_connector_unit_for_model(
            GenericAdapter, '_import_stock_available'
        )
        filters = self.get_filter(product)
        before = self._get_quantity(filters)
        if before != 'empty' and int(before) == int(product.quantity):
            return "The quantity in prestashop is already set to %s. Nothing to do" % product.quantity

        adapter.export_quantity(filters, int(product.quantity))
        after = self._get_quantity(filters)
        if before == 'empty' and after == 'empty':
            return "No stock move found in prestashop, for product %s OpenERP stock %s" % (product.default_code, product.quantity)
        if int(after) != int(product.quantity):
            raise orm.except_orm(
                _('Prestashop Error'),
                _("OpenERP ask to set the quantity to %s"
                  " but it's still %s in prestashhop") 
                % (int(product.quantity), after))
        return """
        Product : %s
        Before the synchronisation the quantity on prestashop was %s
        OpenERP ask Prestashop to set the quantity to %s
        After the export the quantity was %s
        """ % (product.default_code, before, product.quantity, after)





@prestashop(replacing=CombinationInventoryExport)
class JobInfoCombinationInventoryExport(CombinationInventoryExport):
    _model_name = ['prestashop.product.combination']

    #UGLY COPY / PASTE not clean way to inherit it :'(
    def _get_quantity(self, ori_filters):
        filters = ori_filters.copy()
        filters['display'] = '[quantity]'

        adapter = self.get_connector_unit_for_model(
            GenericAdapter, '_import_stock_available'
        )
 
        quantities = adapter.get(filters)
        all_qty = 0
        if not quantities['stock_availables']:
            return 'empty'
        quantities = quantities['stock_availables']['stock_available']
        if isinstance(quantities, dict):
            quantities = [quantities]
        for quantity in quantities:
            all_qty += int(quantity['quantity'])
        return all_qty

    def run(self, binding_id, fields):
        """ Export the product inventory to Prestashop """
        product = self.session.browse(self.model._name, binding_id)
        adapter = self.get_connector_unit_for_model(
            GenericAdapter, '_import_stock_available'
        )
        filters = self.get_filter(product)
        before = self._get_quantity(filters)
        if before != 'empty' and int(before) == int(product.quantity):
            return "The quantity in prestashop is already set to %s. Nothing to do" % product.quantity
 
        adapter.export_quantity(filters, int(product.quantity))
        after = self._get_quantity(filters)
        if before == 'empty' and after == 'empty':
            return "No stock move found in prestashop, for product %s OpenERP stock %s" % (product.default_code, product.quantity)
        if int(after) != int(product.quantity):
            raise orm.except_orm(
                _('Prestashop Error'),
                _("OpenERP ask to set the quantity to %s"
                  " but it's still %s in prestashhop") 
                % (int(product.quantity), after))
        return """
        Product : %s
        Before the synchronisation the quantity on prestashop was %s
        OpenERP ask Prestashop to set the quantity to %s
        After the export the quantity was %s
        """ % (product.default_code, before, product.quantity, after)



