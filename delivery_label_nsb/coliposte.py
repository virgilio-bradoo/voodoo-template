# -*- coding: utf-8 -*-
###############################################################################
#
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


class StockPicking(orm.Model):
    _inherit = 'stock.picking'

    def _prepare_address_postefr(self, cr, uid, pick, context=None):
        address = super(StockPicking, self)._prepare_address_postefr(
            cr, uid, pick, context=context)
        if pick.carrier_type == 'colissimo':
            address['name'] = self._sanitize_company_name(
                cr, uid, pick.partner_id, pick.partner_id.name,
                context=context)[:35]
        return address
