# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2013 Akretion
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


from openerp.osv import orm
from openerp.addons.delivery_label_nsb.stock import StockPickingAbstract


class ChronopostPrepareWebservice(orm.Model):
    _inherit = 'chronopost.prepare.webservice'


    def get_chronopost_account(self, cr, uid, company, pick, context=None):
        """
            If your company use more than one chronopost account, implement
            your method to return the right one depending of your picking.
        """
        res = False
        company_customer = False
        partner = pick.partner_id
        parent_partner = partner.parent_id or partner
        for presta in parent_partner.prestashop_bind_ids:
            company_customer = presta.company
        for account in company.chronopost_account_ids:
            is_pro = account.is_pro
            if (company and is_pro) or (not company and not is_pro):
                res = account
        if not res:
            raise orm.except_orm('Error', 'The accounts for your company are not well configured!')
        return res


class chronopost_prepare_webservice(orm.Model):
    _inherit = 'chronopost.prepare.webservice'


    def _prepare_recipient(self, cr, uid, picking, context=None):
        partner = picking.partner_id
        recipient_data = self._prepare_address(cr, uid, partner, context=context)
        if '(Mon adresse)' in partner.name:
            name = partner.name.split('(Mon adresse)')[0]
        else:
            name = partner.name
        recipient_data['name'] = name
        company = partner.prestashop_bind_ids and partner.prestashop_bind_ids[0].company or False
        if company:
            recipient_data['name2'] = company
        else:
            recipient_data['name2'] = ' '
        recipient_data['alert'] = int(self._get_single_option(
                                      picking, 'recipient_alert') or 0)
        return recipient_data

    def _prepare_shipper(self, cr, uid, picking, context=None):
        res = super(chronopost_prepare_webservice, self)._prepare_shipper(cr, uid, picking, context=context)
        name = context.get('chrono_account_name', False)
        if name:
            res['name2'] = name
        return res


    def _prepare_basic_ref(self, cr, uid, picking, context=None):
        presta = False
        presta = picking.partner_id.prestashop_bind_ids or picking.partner_id.parent_id.prestashop_bind_ids
        partner_presta_id = presta and presta[0].prestashop_id or ''
        ref_data = {
            'shipperRef': "12556",
            'recipientRef': partner_presta_id or picking.partner_id.id, #FIXME  Code point relais si chrono relais
        }
        return ref_data

class StockPicking(StockPickingAbstract, orm.Model):
    _inherit = "stock.picking"


    def print_label(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Process only one a single id at a time.'
        label_obj = self.pool['shipping.label']
        label_ids = label_obj.search(cr, uid, [
            ['res_id', 'in', ids],
            ], context=context)
        if label_ids:
            res = super(StockPicking, self).print_label(cr, uid, ids, context=context)
        else:
            self.generate_labels(cr, uid, ids, context=context)
            res = super(StockPicking, self).print_label(cr, uid, ids, context=context)
        return res

class StockPickingOut(StockPickingAbstract, orm.Model):
    _inherit = "stock.picking.out"


    def print_label(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Process only one a single id at a time.'
        label_obj = self.pool['shipping.label']
        label_ids = label_obj.search(cr, uid, [
            ['res_id', 'in', ids],
            ], context=context)
        if label_ids:
            res = super(StockPickingOut, self).print_label(cr, uid, ids, context=context)
        else:
            self.generate_labels(cr, uid, ids, context=context)
            res = super(StockPickingOut, self).print_label(cr, uid, ids, context=context)
        return res

