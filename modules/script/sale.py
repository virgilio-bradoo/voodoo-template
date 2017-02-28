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

from openerp.osv import fields, orm
from openerp.tools.translate import _
import netsvc
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(orm.Model):
    _inherit = 'sale.order'
  
    #TODO move in an abstract model
    def _check_state(self, cr, uid, record_id, state, context=None):
        domain = [
            ('id', '=', record_id),
            ('state', 'in', state),
            ]
        if not self.search(cr, uid, domain, context=context):
            record = self.browse(cr, uid, record_id, context=context)
            raise orm.except_orm(
                _('Error'),
                _('The %s %s is not in the state %s the actual state is %s')
                % (self._name, record_id, state, record.state),
                )
        return True

    def dev_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for sale in self.browse(cr, uid, ids, context=context):
            _logger.info('Cancel sale %s' % sale.id)
            wf_service.trg_validate(uid, 'sale.order', sale.id, 'cancel', cr)
            wf_service.trg_validate(uid, 'sale.order', sale.id, 'action_cancel', cr)
            wf_service.trg_validate(uid, 'sale.order', sale.id, 'invoice_cancel', cr)
            self._check_state(cr, uid, sale.id, ['cancel'], context=context)
        return True
    
    def dev_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        order_line_obj = self.pool['sale.order.line']
        for order in self.browse(cr, uid, ids, context=context):
            order.write({'state':'draft'})
            line_ids = []
            for line in order.order_line:
                line_ids.append(line.id)
            order_line_obj.write(cr, uid, line_ids, {'state':'draft', 'invoiced': False})
            wf_service.trg_delete(uid, 'sale.order', order.id, cr)
            wf_service.trg_create(uid, 'sale.order', order.id, cr)
        return True

    def dev_validate(self, cr, uid, ids, context=None):
        for sale_id in ids:
            res = self.action_button_confirm(cr, uid, [sale_id], context=context)
            sale = self.browse(cr, uid, sale_id, context=context)
            print sale.amount_total, sale.amount_tax
            print sale.prestashop_bind_ids[0].total_amount, sale.prestashop_bind_ids[0].total_amount_tax
            self._check_state(cr, uid, sale_id, ['progress', 'manual'], context=context)
        return True

    def script_remove_refund_product(self, cr, uid, ids, force_total=False, context=None):
        uid2product_id = {
            9: 10, #admin nsb concept
            }
 
        if not ids:
            ids = self.search(cr, uid, [
                ('state', '=', 'draft'),
                ('date_order', '<', '2014-01-01'),
                ('date_order', '>', '2012-12-01'),
                ('order_line.product_id', '=', uid2product_id[uid]),
                '|',
                ('order_line.name', '=like', 'Discount V%'),
                ('order_line.name', '=like', 'Discount A%'),
                ], context=context)
        for sale in self.browse(cr, uid, ids, context=context):
            try:
                total_discount = 0
                presta_order = sale.prestashop_bind_ids[0]
                force_tax = False
                if sale.id in [34253]:
                    force_tax = True
                if sale.id in [29166, 28254]:
                    force_total = True
                if presta_order.total_amount == 0 and sale.amount_total <=0:
                    total_discount -= sale.amount_total
                    force_tax = True
                if presta_order.total_amount_tax < 0:
                    force_tax = True
                for line in sale.order_line:
                    #if line.name[0:10] in ['Discount V', 'Discount A']:
                    if line.product_id.id == uid2product_id[uid]:
                        total_discount += line.price_unit
                        line.unlink()
                total_amount = sale.prestashop_bind_ids[0].total_amount
                total_amount -= total_discount
                vals = {'total_amount': total_amount}
                if force_tax:
                    sale = sale.browse()[0]
                    vals['total_amount_tax'] = sale.amount_tax
                if force_total:
                    sale = sale.browse()[0]
                    vals.update({
                        "total_amount": sale.amount_total,
                        "total_amount_tax": sale.amount_tax,
                    })
                presta_order.write(vals)
                sale.dev_validate()
                cr.commit()
            except Exception, e:
                print '=== fail to update sale order ===', sale.name, e
                cr.rollback()
        return True

    def set_intracommunautaire(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            sale.write({'fiscal_position': 13})
            for line in sale.order_line:
                if line.product_id.id == 15:
                    line.write({'account_id': 27981, 'tax_id': [(6, 0, [362])]})
                else:
                    line.write({'account_id': 27979, 'tax_id': [(6, 0, [362])]})
            sale.dev_validate()
        return True

    def add_delta(self, cr, uid, ids, context=None):
        line_obj = self.pool['sale.order.line']
        for sale in self.browse(cr, uid, ids, context=context):
            diff = sale.amount_total - sale.prestashop_bind_ids[0].total_amount
            line_obj.create(cr, uid, {
                'order_id': sale.id,
                'name': 'DELTA',
                'tax_id': [[6, 0, [414]]],
                'account_id': 6688,
                'price_unit': -diff,
                }, context=context)
            sale.dev_validate()
        return True

    def dev_cancel_all(self, cr, uid, ids, context=None):
        invoice_obj = self.pool['account.invoice']
        for order in self.browse(cr, uid, ids, context=context):
            for invoice in order.invoice_ids:
                invoice.dev_cancel()
            inv_id = invoice_obj.search(cr, uid, [
                ['origin', '=', order.name],
                ['state', '!=', 'cancel'],
                ], context=context)
            if inv_id:
                invoice_obj.dev_cancel(cr, uid, inv_id, context=context)
            order.dev_draft()
            order.dev_cancel()
        return True
