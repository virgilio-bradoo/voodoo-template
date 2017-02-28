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
import netsvc
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'
    
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
    
    def dev_unreconcile(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context=context):
            _logger.info('Unreconcile invoice %s' % inv.id)
            for payment in inv.payment_ids:
                if payment.move_id.writeoff:
                    continue
                if payment.reconcile_id:
                    payment.reconcile_id.unlink()
                    break
                elif payment.reconcile_partial_id:
                    payment.reconcile_partial_id.unlink()
                    break
        return True
    
    def dev_open(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids, context=context):
            _logger.info('Open invoice %s' % inv.id)
            inv.dev_unreconcile()
            wf_service.trg_validate(uid, 'account.invoice', inv.id, 'open_test', cr)
            self._check_state(cr, uid, inv.id, ['open'], context=context)
        return True

    def dev_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids, context=context):
            _logger.info('Cancel invoice %s' % inv.id)
            if inv.state == 'paid':
                inv.dev_open()
            elif inv.payment_ids:
                inv.dev_unreconcile()
            wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
            self._check_state(cr, uid, inv.id, ['cancel'], context=context)
        return True

    def dev_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids, context=context):
            _logger.info('Set to draft invoice %s' % inv.id)
            if inv.state in ('open', 'paid'):
                inv.dev_cancel()
            inv.action_cancel_draft()
            self._check_state(cr, uid, inv.id, ['draft'], context=context)
        return True

    def dev_validate(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            self.button_reset_taxes(cr, uid, [inv_id], context=context)
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
            self._check_state(cr, uid, inv_id, ['open', 'paid'], context=context)
        return True


    ################ SPECIFIC FUNCTION #################"""
    def script_remove_refund_product(self, cr, uid, ids, context=None):
        inv_obj = self.pool['account.invoice']
        inv_line_obj = self.pool['account.invoice.line']
        uid2product_id = {
            9: 10, #admin nsb concept
            }
        if not ids:
            ids = inv_obj.search(cr, uid, [
                #('invoice_line.product_id', '=', uid2product_id[uid]),
                ('date_invoice', '>=', '2014-01-01'),
                '|',
                ('invoice_line.name', '=like', 'Discount V%'),
                ('invoice_line.name', '=like', 'Discount avoir%'),
                ], context=context)
        for inv_id in ids:
            _logger.info('Remove refund product on invoice %s' % inv_id)
            self.dev_draft(cr, uid, [inv_id], context=context)
            line_ids =  inv_line_obj.search(cr, uid, [
                ('name', '=like', 'Discount V%'),
                ('invoice_id', '=', inv_id),
                ], context=context)
            _logger.info('Remove lines %s' % line_ids)
            inv_line_obj.unlink(cr, uid, line_ids, context=context)
            self.dev_validate(cr, uid, [inv_id], context=context)
            cr.commit()
        return True



    def add_delta_from_order(self, cr, uid, order_name, total_amount, context=None):
        inv_id = self.search(cr, uid, [['origin', '=', order_name]], context=context)
        if not inv_id:
            raise orm.except_orm(_('Error'), _('Not invoice found'))
        else:
            inv_id = inv_id[0]
        return self.add_delta(cr, uid, inv_id, total_amount, context=context)

    def add_delta(self, cr, uid, inv_id, total_amount, context=None):
        line_obj = self.pool['account.invoice.line']
        inv = self.browse(cr, uid, inv_id, context=context)
        inv.dev_draft()
        diff = inv.amount_total - total_amount
        line_obj.create(cr, uid, {
            'invoice_id': inv.id,
            'name': 'DELTA',
            'invoice_line_tax_id': [[6, 0, [414]]],
            'account_id': 6688,
            'price_unit': -diff,
            }, context=context)
        inv.dev_validate()
        return True

    def clean_refund(self, cr, uid, ids, context=None):
        order_obj = self.pool['sale.order']
        if not ids:
            ids = self.search(cr, uid, [
                ('type', '=', 'out_refund'),
                ('state', '!=', 'cancel'),
                ('date_invoice', '>', '2013-01-01'),
                ], context=context)
        for refund in self.browse(cr, uid, ids, context=context):
            domain = [
                ('state', '=', 'cancel'),
                ('name', '=', refund.origin),
            ] 
            if order_obj.search(cr, uid, domain, context=context):
                refund.dev_cancel()
        return True

    def _fix_tax(self, cr, uid, invoice):
        print 'backe to draft'
        invoice.dev_draft()
        if invoice.date_invoice < '2014-01-01':
            tax_id = 364 #19.6
        else:
            tax_id = 314
        for line in invoice.invoice_line:
            if not line.invoice_line_tax_id:
                line.write({'invoice_line_tax_id':  [(6,0, [tax_id])]})
        invoice.dev_validate()

    def fix_invoice_missing_tax(self, cr, uid, ids, context=None):
        #ID JOURNAL : 66 => vente cdiscount
        #Récupérer les factures
        #pour chaque facture récupérer le paiement
        for invoice_id in ids:
            invoice = self.browse(cr, uid, invoice_id, context=context) 
            self._fix_tax(cr, uid, invoice)
        return True



class AccountMove(orm.Model):
    _inherit = 'account.move'

    def check_valid_vat(self, cr, uid, ids, context=None):
        AccountRequiredTax = [6688, 6696]
        move = self.browse(cr, uid, ids[0], context=context)
        check = False
        total = 0
        total_tax = 0
        for line in move.line_id:
            if line.account_id.id in AccountRequiredTax:
                total += line.debit - line.credit
            if line.account_id.id == 6284:
                total_tax = line.debit - line.credit
        if total or total_tax:
            print 'total', total
            print 'total_vat', total_tax
            min_tax = abs(total_tax * 0.96)
            max_tax = abs(total_tax * 1.04)
            computed_tax = abs(total * 0.196)
            print 'min_tax', min_tax
            print 'max_tax', max_tax
            print 'computed taxe', computed_tax
            return min_tax < computed_tax < max_tax
        return True
 
