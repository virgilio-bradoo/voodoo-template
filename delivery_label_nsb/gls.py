# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm  # fields

SIZE = 200


class StockPicking(orm.Model):
    _inherit = "stock.picking"

    # Due to this bug https://bugs.launchpad.net/openobject-addons/+bug/1169998
    # you need do declare new fields in both picking models
    def __init__(self, pool, cr):
        super(StockPicking, self).__init__(pool, cr)
        self._columns['carrier_tracking_ref'].size = SIZE

    def _prepare_address_name_gls(self, cr, uid, partner, context=None):
        res = super(StockPicking, self)._prepare_address_name_gls(
            cr, uid, partner, context=context)
        res['consignee_name'] = self._sanitize_company_name(
            cr, uid, partner, res['consignee_name'], context=context)
        res['contact'] = res['contact'].replace(
            '(Mon adresse)', '')
        return res

    def _customize_gls_picking(self, cr, uid, picking, context=None):
        super(StockPicking, self)._customize_gls_picking(
            cr, uid, picking, context=context)
        tracking_lst = []
        if picking.carrier_tracking_ref:
            tracking_lst.append(picking.carrier_tracking_ref)
        track_from_trackings = sorted(set(
            line.tracking_id.serial
            for line in picking.move_lines
            if line.tracking_id
        ))
        tracking_lst.extend(track_from_trackings)
        tracking_string = ' '.join(tracking_lst)
        self.pool['stock.picking.out'].write(
            cr, uid, picking.id, {'carrier_tracking_ref': tracking_string},
            context=context)
        return True


class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'

    def __init__(self, pool, cr):
        super(StockPickingOut, self).__init__(pool, cr)
        self._columns['carrier_tracking_ref'].size = SIZE
