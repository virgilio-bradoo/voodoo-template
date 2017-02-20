# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2011-2014 Akretion (http://www.akretion.com).
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


from openerp.osv import orm
from openerp.tools.translate import _
from openerp import netsvc
import logging

_logger = logging.getLogger(__name__)
LOGISTIFLEX_ADDRESS_ID = 42861
IP_BOX = 'localhost'


class StockPickingAbstract():

    def print_label(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Process only one a single id at a time.'
        label_obj = self.pool['shipping.label']
        label_ids = label_obj.search(cr, uid, [
            ['res_id', 'in', ids],
            ], context=context)
        action_list = []
        for label in label_obj.browse(cr, uid, label_ids, context=context):
            action_list.append({
                'url': 'https://%s/cups/printData' % IP_BOX,
                'params': {
                    'args': ['zebra', label.datas],
                    'kwargs': {'options': {'raw': True}},
                    }
                })
        
        picking = self.browse(cr, uid, ids, context=context)[0]
        copy_number = 1
        if picking.colipostefr_send_douane_doc:
            self.pool['stock.picking.out'].cn23_trigger(
                cr, uid, ids, context=context)
            copy_number = 3
        cn_obj = self.pool['ir.attachment']
        cn_ids = cn_obj.search(cr, uid, [
                    ['res_id', 'in', ids],
                    ['name', 'ilike', 'CN23%.pdf'],
                ], context=context)
        if cn_ids:
            action_a4 = {}
            cn = cn_obj.browse(cr, uid, cn_ids, context=context)[0]
            action_cn23 = {
                'url' : 'https://%s/cups/printData' % IP_BOX,
                'params': {
                    'args': ['HP_LaserJet_400_M401d', cn.datas],
                    'kwargs': {'options': {'raw': True, 'copies': copy_number}},
                }
            }
            action_list.insert(0, action_cn23)

        if label_ids and picking.sale_id and picking.sale_id.fiscal_position:
            fiscal_position = picking.sale_id.fiscal_position.name
            invoice_ids = []
            if fiscal_position == 'Import/Export + DOM-TOM':
                invoice_ids = [i.id for i in picking.sale_id.invoice_ids]
            for invoice_id in invoice_ids:
                service = netsvc.LocalService('report.account.invoice')
                (result, format) = service.create(
                    cr, uid, [invoice_id], {'model': 'account.invoice'}, context)
                attach_obj = self.pool['ir.attachment']
                invoice_attach_ids = attach_obj.search(cr, uid, [
                    ['res_id', '=', invoice_id],
                    ['res_model', '=', 'account.invoice'],
                ], context=context)
                if invoice_attach_ids:
                    invoice_attach = attach_obj.browse(
                            cr, uid, invoice_attach_ids, context=context)[0]
                    action_invoice = {
                        'url' : 'https://%s/cups/printData' % IP_BOX,
                        'params': {
                            'args': ['HP_LaserJet_400_M401d', invoice_attach.datas],
                            'kwargs': {'options': {'raw': True, 'copies': 5}},
                        }
                    }
                    action_list.append(action_invoice)
        _logger.info('PRINT LABEL %s' % action_list)
        return {
            'type': 'ir.actions.act_proxy',
            'action_list': action_list,
            }

    def _get_label_sender_address(self, cr, uid, picking, context=None):
        partner_obj = self.pool['res.partner']
        return partner_obj.browse(
            cr, uid, LOGISTIFLEX_ADDRESS_ID, context=context)


class StockPickingOut(orm.Model):
    _inherit = "stock.picking.out"

    def cn23_trigger(self, cr, uid, ids, context=None):
        service = netsvc.LocalService('report.stock.picking.cn23')
        (result, format) = service.create(
            cr, uid, ids, {'model': 'stock.picking.out'}, context)
        return True


class StockPicking(orm.Model):
    _inherit = 'stock.picking'

    def _sanitize_company_name(self, cr, uid, partner_id, name, context=None):
        " Name can be extracted from partner_id or set to a particular value"
        if '(Mon adresse)' in name:
            name = name.split('(Mon adresse)')[0]
        if partner_id.company:
            name = '%s, %s' % (partner_id.company, name)
        return name


class stock_split_into(orm.TransientModel):
    _inherit = "stock.split.into"
    _description = "Split into"

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        context.update({
            'form_view_ref': None,
            'tree_view_ref': None,
        })
        return super(stock_split_into, self).fields_view_get(
            cr, user, view_id=None, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
