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
        for product_sup in supplier_info_obj.browse(cr, uid, supplier_ids, context=context):
            if product_sup.product_code:
               supplier_code = unidecode(product_sup.product_code)
            else:
               supplier_code = 'No code for product id : %s' % product_sup.product_id.id
            missing_products_content += '\n%s' % supplier_code
        
        file_ids = []
        if codes:
            output = base64.b64encode(missing_codes_content)
            file_ids.append(self.pool.get('file.wizard').create(cr, uid, {'file': output, 'name': 'missing_codes' + '.csv'}))
        if supplier_ids:
            output = base64.b64encode(missing_products_content)
            file_ids.append(self.pool.get('file.wizard').create(cr, uid, {'file': output, 'name': 'missing_products' + '.csv'}))
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

        ref_not_found = []
        products_updated = []
        supplier_info_obj = self.pool['product.supplierinfo']
        product_obj = self.pool['product.product']
        all_product_ids = supplier_info_obj.search(cr, uid, [('name', '=', importer.partner_id.id)], context=context)
        session = ConnectorSession(cr, uid, context=context)
        for row in csv_reader:
            if row.get('supplier_ref', False):
                product_ids = supplier_info_obj.search(cr, uid, [
                                         ('id', 'in', all_product_ids),
                                         ('product_code', '=', row['supplier_ref'])],
                                        context=context)
                if product_ids:
                    product_id = product_ids[0]
                    vals = {}
                    if row.get('purchase_price', False):
                        vals['manual_cost_price'] = float(row.get('purchase_price').replace(',', '.'))
                    if row.get('sale_price', False):
                        vals['list_price'] = float(row.get('sale_price').replace(',', '.'))
                    product_sup = supplier_info_obj.browse(cr, uid, [product_id], context=context)[0]
                    product = product_sup.product_id
                    tax_obj = self.pool['account.tax']
                    taxes = [tax.related_inc_tax_id for tax in product.taxes_id if tax.related_inc_tax_id]
                    taxes = tax_obj._unit_compute(cr, uid, taxes, vals['list_price'], product=product.id)
                    taxe_amount = sum([t['amount'] for t in taxes])
                    taxe_incl = vals['list_price'] + taxe_amount
                    vals['list_price_tax_inc'] = taxe_incl
                    import_price_from_supplier_file.delay(session, [product.id], vals)
                    _logger.info('Create import price job for product %s' % product.id)
                    #product_obj.write(cr, uid, [product.id], vals, context=context)
                    products_updated.append(product_id)
                else:
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
