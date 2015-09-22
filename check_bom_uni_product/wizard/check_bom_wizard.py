# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2015 Akretion
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
Wizard to to check uni product bom configuration
"""

from openerp.osv import orm, fields
from openerp.tools.translate import _
import csv
import base64
import cStringIO


class CheckBomWizard(orm.TransientModel):
    _name = "check.bom.wizard"

    def get_query(self, cr, uid, context=None):
        company_id = self.pool['res.users']._get_company(
            cr, uid, context=context)
        query = """
            SELECT b.id
            FROM mrp_bom b
            LEFT JOIN mrp_bom child
                ON child.bom_id = b.id
            LEFT JOIN product_product p
                ON b.product_id = p.id
            LEFT JOIN product_template t
                ON p.product_tmpl_id = t.id
            WHERE b.company_id = %s
                AND b.active = true
                AND p.active = true
                AND t.supply_method = 'produce'
            GROUP BY b.id
            HAVING count(child.id) = 1
        """ % (company_id,)
        print query
        return query

    def check_bom_configuration(self, cr, uid, ids, context=None):
        bom_obj = self.pool['mrp.bom']
        for wizard in self.browse(cr, uid, ids, context=context):
            # Get bom with one line only
            query = self.get_query(cr, uid, context=context)
            cr.execute(query)
            bom_query_ids = cr.fetchall()
            print bom_query_ids
            if bom_query_ids:
                bom_ids = [b[0] for b in bom_query_ids]
            product_config = []
            ref_config = []
            for bom in bom_obj.browse(cr, uid, bom_ids, context=context):
                product_bom = bom.product_id
                if product_bom.procure_method == 'make_to_stock' or \
                        product_bom.supply_method == 'buy':
                    product_config.append(product_bom.default_code)
                presta_bom_ref = ''
                for presta_product_bom in product_bom.prestashop_bind_ids:
                    presta_bom_ref = presta_product_bom.reference
                    break
                child_bom_product = bom.bom_lines[0].product_id
                presta_child_ref = ''
                for presta_product_child in child_bom_product.prestashop_bind_ids:
                    presta_child_ref = presta_product_child.reference
                if not presta_child_ref:
                    for presta_product_child in child_bom_product.prestashop_combinations_bind_ids:
                        presta_child_ref = presta_product_child.reference
                if not (presta_child_ref and presta_bom_ref and presta_bom_ref == presta_child_ref):
                    supplier = child_bom_product.seller_id and child_bom_product.seller_id.name or 'No supplier'
                    ref_config.append([supplier, product_bom.default_code, child_bom_product.default_code])

            file_ids = self.prepare_output_files(cr, uid, product_config, ref_config)
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


    def prepare_output_files(self, cr, uid, product_config, ref_config):
        prod_obj = self.pool['product.product']
        file_ids = []
        if product_config:
            file_prod = cStringIO.StringIO()
            writer_prod = csv.writer(file_prod, delimiter=';')
            writer_prod.writerow(['Product Ref'])
            for code in product_config:
                writer_prod.writerow([code])
            data = base64.encodestring(file_prod.getvalue())
            file_ids.append(self.pool['file.wizard'].create(
                cr, uid,
                {'file': data, 'name': 'product_configuration_problem' + '.csv'}))
        if ref_config:
            file_bom = cStringIO.StringIO()
            writer_bom = csv.writer(file_bom, delimiter=';')
            writer_bom.writerow(['Fournisseur', 'Pack Ref', 'Composant Ref'])
            for config_list in ref_config:
                writer_bom.writerow(config_list)
            data = base64.encodestring(file_bom.getvalue())
            file_ids.append(self.pool['file.wizard'].create(
                cr, uid,
                {'file': data, 'name': 'bom_configuration_problem' + '.csv'}))
        return file_ids
