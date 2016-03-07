# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2014-2015 Akretion
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

"""
Wizard to import product prices by supplier
"""

from openerp.osv import orm, fields
from openerp.tools.translate import _
import csv
import base64
from csv import Dialect
import StringIO
from unidecode import unidecode
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job
import logging
_logger = logging.getLogger(__name__)


class ImportProductPrice(orm.TransientModel):
    _name = "import.product.price"

    _columns = {
        'partner_id': fields.many2one('res.partner',
                                      'Supplier',
                                      required=True,
                                      domain=[('supplier','=','True')]),
        'input_price': fields.binary('Product Price File', required=True),
        'file_name': fields.char('File Name', size=128),
    }

    def prepare_output_files(self, cr, uid, codes, supplier_ids, context=None):
        supplier_info_obj = self.pool['product.supplierinfo']
        product_obj = self.pool['product.product']
        missing_codes_content = 'Missing references'
        for code in codes:
            missing_codes_content += '\n%s' % code
        missing_products_content = 'Missing Products'
        default_codes = []
        if supplier_ids:
            cr.execute("""
                SELECT p.default_code
                FROM product_product p LEFT JOIN product_template t ON p.product_tmpl_id = t.id 
                LEFT JOIN product_supplierinfo s ON s.product_id = t.id
                WHERE s.id in %s """, (tuple(supplier_ids),))
            default_codes = cr.fetchall()
        for default_code in default_codes:
            if default_code[0]:
                product_code = unidecode(default_code[0])
                missing_products_content += '\n%s' % product_code
        file_ids = []
        if codes:
            output = base64.b64encode(missing_codes_content)
            file_ids.append(self.pool.get('file.wizard').create(cr, uid, {'file': output, 'name': 'references_not_found' + '.csv'}))
        if supplier_ids:
            output = base64.b64encode(missing_products_content)
            file_ids.append(self.pool.get('file.wizard').create(cr, uid, {'file': output, 'name': 'products_not_updated' + '.csv'}))
        return file_ids

    def import_product_price(self, cr, uid, wid, context=None):
        if isinstance(wid, list):
            wid = wid[0]
        if context is None:
            context = {}
        importer = self.browse(cr, uid, wid, context)
        file_stream = importer.input_price
        file_stream = base64.b64decode(file_stream)
        file_stream  = '\n'.join(file_stream.splitlines())
        output = StringIO.StringIO(file_stream)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(file_stream, delimiters=';,')
        csv_reader = csv.DictReader(output, dialect=dialect)
        company_id = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.id
        ref_not_found = []
        products_updated = []
        supplier_info_obj = self.pool['product.supplierinfo']
        product_obj = self.pool['product.product']
        price_list = importer.partner_id.property_product_pricelist_purchase or False
        currency_purchase_partner = price_list and price_list.currency_id or False
        dollar_currency = False
        pound_currency = False
        purchase_field_position = 0
        if currency_purchase_partner and currency_purchase_partner.name == 'USD':
            dollar_currency = True
            purchase_field_position = 1
        elif currency_purchase_partner and currency_purchase_partner.name == 'GBP':
            pound_currency = True
            purchase_field_position = 2
        #all_product_ids = supplier_info_obj.search(cr, uid, [('name', '=', importer.partner_id.id), ('product_id.purchase_ok', '=', True), ('product_id.sale_ok', '=', True)], context=context)
        # We want supplier info only for active product and the active field is 
        # on product, easier with sql request
        cr.execute("""
            SELECT s.id 
            FROM product_supplierinfo s LEFT JOIN product_template t ON s.product_id = t.id 
            LEFT JOIN product_product p ON p.product_tmpl_id = t.id 
            WHERE s.name = %s 
                AND t.purchase_ok = true 
                AND t.sale_ok = true 
                AND p.active = true
                AND s.company_id = %s """, (importer.partner_id.id,company_id,))
        all_product_ids = [sup_id[0] for sup_id in cr.fetchall()]
        session = ConnectorSession(cr, uid, context=context)
        for row in csv_reader:
            if row.get('supplier_ref', False):
                product_sup_ids = supplier_info_obj.search(cr, uid, [
                                         ('id', 'in', all_product_ids),
                                         ('product_code', '=', row['supplier_ref'])],
                                        context=context)
                for product_sup_id in product_sup_ids:
                    vals = {}
                    if row.get('purchase_price', False):
                        if dollar_currency:
                            vals['dollar_purchase_price'] = float(row.get('purchase_price').replace(',', '.'))
                        elif pound_currency:
                            vals['pound_purchase_price'] = float(row.get('purchase_price').replace(',', '.'))
                        else:
                            vals['manual_cost_price'] = float(row.get('purchase_price').replace(',', '.'))
                    if row.get('sale_price', False):
                        vals['list_price'] = float(row.get('sale_price').replace(',', '.'))
                    product_sup = supplier_info_obj.browse(cr, uid, [product_sup_id], context=context)[0]
                    template = product_sup.product_id
                    cr.execute("SELECT manual_cost_price, dollar_purchase_price, pound_purchase_price FROM product_product WHERE product_tmpl_id = %s", (template.id,))
                    product_prices = cr.fetchall()
                    #product = product_obj.read(cr, uid, product_ids[0], ['list_price', 'manual_cost_price'], context=context)
                    list_price_diff = abs(template.list_price - vals.get('list_price', template.list_price))
                    cost_price = product_prices[0][purchase_field_position] or 0
                    cost_price_diff = abs(cost_price - vals.get('manual_cost_price', product_prices[0][0]))
                    tax_obj = self.pool['account.tax']
                    taxes = [tax.related_inc_tax_id for tax in template.taxes_id if tax.related_inc_tax_id]
                    taxes = tax_obj._unit_compute(cr, uid, taxes, vals['list_price'], product=template.id)
                    taxe_amount = sum([t['amount'] for t in taxes])
                    taxe_incl = vals['list_price'] + taxe_amount
                    vals['list_price_tax_inc'] = taxe_incl
                    if list_price_diff > 0.02 or cost_price_diff > 0.02:
                        import_price_from_supplier_file.delay(session, [template.id], vals)
                        _logger.info('Create import price job for products %s' % [template.id])
                    else:
                        _logger.info('No change for product %s' % [template.id])
                    products_updated.append(product_sup_id)
                if not product_sup_ids:
                    ref_not_found.append(row['supplier_ref'])
        missing_product_ids = [x for x in all_product_ids if x not in products_updated]
        file_ids = self.prepare_output_files(cr, uid, ref_not_found, missing_product_ids)
        multi_file_id = self.pool.get('multi.file.wizard').create(cr, uid, {'file_ids': [(6, False, file_ids)]})
        result = {
            'name': _('Notification'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'multi.file.wizard',
            'res_id': multi_file_id,
            'target': 'new',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        return result

@job
def import_price_from_supplier_file(session, product_ids, vals):
    "Import product price from file"
    session.context.update({'update_price': True})
    session.write('product.product', product_ids, vals)
