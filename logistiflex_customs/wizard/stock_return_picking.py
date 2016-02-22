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

from openerp.osv import osv
import time
from openerp import SUPERUSER_ID, netsvc

class stock_return_picking(osv.osv_memory):
    _inherit = "stock.return.picking"

    def create_intercompany_return(self, cr, uid, moves_qties, supplier_customer_moves, pick, context=None):
        move_obj = self.pool['stock.move']
        uom_obj = self.pool['product.uom']
        pick_obj = self.pool['stock.picking']
        invoice_obj = self.pool['account.invoice']
        invoice_line_obj = self.pool['account.invoice.line']
        partner_obj = self.pool['res.partner']
        wf_service = netsvc.LocalService("workflow")
        user_move_dict = {}
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        for sup_move_id in moves_qties.keys():
            new_uid = move_obj.get_record_id_user(cr, uid, sup_move_id, context=context)
            if not user_move_dict.get(new_uid, []):
                user_move_dict[new_uid] = [sup_move_id]
            else:
                user_move_dict[new_uid].append(sup_move_id)

        for company_uid, sup_move_ids in user_move_dict.iteritems():
            first_sup_move = move_obj.browse(cr, company_uid, sup_move_ids[0], context=context)
            new_pick_name = self.pool.get('ir.sequence').get(
                cr, uid, 'stock.picking.in')
            picking_name = '%s-%s-intercompany-return' % (new_pick_name, pick.name)
            return_picking_vals = {
                'name': picking_name,
                'type': 'in',
                'date':date_cur, 
                'invoice_state': 'none',
                'partner_id': first_sup_move.picking_id and \
                              first_sup_move.picking_id.partner_id and \
                              first_sup_move.picking_id.partner_id.id or False,
            }
            picking_id = pick_obj.create(cr, company_uid, return_picking_vals, context=context)
            for sup_move_id in sup_move_ids:
                qty = moves_qties[sup_move_id]
                sup_move = move_obj.browse(cr, company_uid, sup_move_id, context=context)
                return_move_id= move_obj.copy(cr, company_uid, sup_move_id, {
                    'product_qty': qty,
                    'product_uos_qty': uom_obj._compute_qty(cr, company_uid, sup_move.product_uom.id, qty, sup_move.product_uos.id),
                    'picking_id': picking_id, 
                    'state': 'draft',
                    'location_id': sup_move.location_dest_id.id, 
                    'location_dest_id': sup_move.location_id.id,
                    'date': date_cur,
                    'prodlot_id': sup_move.prodlot_id and sup_move.prodlot_id.id or False
                })
                move_obj.write(cr, company_uid, [sup_move_id], {'move_history_ids2':[(4,return_move_id)]}, context=context)
            wf_service.trg_validate(company_uid, 'stock.picking', picking_id, 'button_confirm', cr)
            pick_obj.validate(cr, company_uid, [picking_id], context=context)
            #Create customer refunds intercompany where customer is company which sell to end customer
            # and supplier is company to supply the customer company


            sup_company_id = first_sup_move.company_id.id
            sup_refund_partner_id = first_sup_move.picking_id and \
                                    first_sup_move.picking_id.partner_id and \
                                    first_sup_move.picking_id.partner_id.id or False
            cus_company_id = pick.company_id.id
            cus_refund_partner_id = partner_obj.find_company_partner_id(
                cr, uid, sup_company_id ,cus_company_id,
                context=context)
            origin = pick.name
            sup_refund_for_customer_vals = invoice_obj._get_refund_vals(
                cr, company_uid, sup_refund_partner_id, 'out_refund',
                sup_company_id, origin, context=context)
            sup_refund_for_customer_id = invoice_obj.create(
                cr, company_uid, sup_refund_for_customer_vals, context=context)
            cus_refund_for_supplier_vals = invoice_obj._get_refund_vals(
                cr, uid, cus_refund_partner_id, 'in_refund', cus_company_id,
                origin, context=context)
            cus_refund_for_supplier_id = invoice_obj.create(
                cr, uid, cus_refund_for_supplier_vals, context=context)

            #Create refund lines intercompany
            
            for sup_move_id in sup_move_ids:
                cus_move = supplier_customer_moves[sup_move_id]
                sup_move = move_obj.browse(cr, company_uid, sup_move_id, context=context)
                qty = sup_move.product_qty
                price = sup_move.sale_line_id.price_unit
                origin = picking_name
                sup_line_vals = invoice_obj.get_refund_line_vals(
                    cr, company_uid, sup_refund_partner_id,
                    first_sup_move.product_id.id, qty, price, origin, sup_company_id, context=context)
                sup_line_vals.update({'invoice_id': sup_refund_for_customer_id})
                invoice_line_obj.create(cr, company_uid, sup_line_vals, context=context)

                cus_line_vals = invoice_obj.get_refund_line_vals(
                    cr, uid, cus_refund_partner_id,
                    cus_move.product_id.id, qty, price, origin, cus_company_id, context=context)
                cus_line_vals.update({'invoice_id': cus_refund_for_supplier_id})
                invoice_line_obj.create(cr, uid, cus_line_vals, context=context)
            wf_service.trg_validate(company_uid, 'account.invoice',
                                        sup_refund_for_customer_id, 'invoice_open', cr)
            wf_service.trg_validate(uid, 'account.invoice',
                                        cus_refund_for_supplier_id, 'invoice_open', cr)
        return True


    def create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {} 
        move_obj = self.pool['stock.move']
        pick_obj = self.pool['stock.picking']
        record_id = context and context.get('active_id', False) or False
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        return_record = self.browse(cr, uid, ids[0], context=context)
        sup_moves_qties = {}
        supplier_customer_moves = {}
        if pick.type != 'out':
            return super(stock_return_picking, self).create_returns(
                cr, uid, ids, context=context)
        for line in return_record.product_return_moves:
            original_move = line.move_id
            intercompany_linked_move_ids = move_obj.search(
                cr, SUPERUSER_ID, [('is_intercompany', '=', True),
                                   ('intercompany_move_id', '=', original_move.id)])
            if intercompany_linked_move_ids:
                if len(intercompany_linked_move_ids) > 1:
                    raise
                inter_move = move_obj.browse(
                    cr, SUPERUSER_ID, intercompany_linked_move_ids[0],
                    context=context)
                if inter_move.state  != 'done':
                    raise
                sup_moves_qties[inter_move.id] = line.quantity
                supplier_customer_moves[inter_move.id] = original_move
                line.unlink()
        if sup_moves_qties:
            self.create_intercompany_return(
                cr, uid, sup_moves_qties, supplier_customer_moves, pick, context=context)

        return_record = self.browse(cr, uid, ids[0], context=context)
        if return_record.product_return_moves:
            return super(stock_return_picking, self).create_returns(
                cr, uid, ids, context=context)
        else:
            return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
