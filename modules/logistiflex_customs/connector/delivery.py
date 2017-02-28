# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Guewen Baconnier, Sébastien Beau, David Béal
#    Copyright (C) 2010 BEAU Sébastien
#    Copyright 2011-2013 Camptocamp SA
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

from openerp.osv import fields, orm
from .backend import prestashop_logistiflex
from openerp.addons.prestashoperpconnect.delivery import CarrierImportMapper
from openerp.addons.connector.unit.mapper import mapping


class PrestashopDeliveryCarrier(orm.Model):
    _inherit = 'prestashop.delivery.carrier'

    _columns = {
        'shipping_state_id': fields.many2one(
            'prestashop.sale.order.state',
            string='Shipping state'
        ),
    }

@prestashop_logistiflex
class LogistiflexCarrierImportMapper(CarrierImportMapper):

    @mapping
    def shipping_state_id(self, record):
        # prendre le dernier carrier ayant la meme référence
        # et récupérer le openerp id
        res = {}
        prestashop_carrier_obj = self.session.pool['prestashop.delivery.carrier']
        existing_carrier_ids = prestashop_carrier_obj.search(
            self.session.cr,
            self.session.uid,
            [('id_reference', '=', record['id_reference']),
             ('backend_id', '=', self.backend_record.id)],
        )
        same_presta_ids_carrier = prestashop_carrier_obj.search(
            self.session.cr,
            self.session.uid,
            [('id_reference', '=', record['id_reference']),
             ('backend_id', '=', self.backend_record.id),
             ('prestashop_id', '=', int(record['id']))],
        )
        #case it is an update
        if same_presta_ids_carrier:
            existing_carrier = prestashop_carrier_obj.browse(
                self.session.cr,
                self.session.uid,
                same_presta_ids_carrier)[0]
            res['shipping_state_id'] = existing_carrier.shipping_state_id and \
                                       existing_carrier.shipping_state_id.id or False
        #case new carrier in prestashop but exists in OE
        elif existing_carrier_ids:
            existing_carrier = prestashop_carrier_obj.browse(
                self.session.cr,
                self.session.uid,
                existing_carrier_ids)[-1]
            if existing_carrier.shipping_state_id:
                res['shipping_state_id'] = existing_carrier.shipping_state_id.id
            else:
                res['shipping_state_id'] = False
        else:
            res['shipping_state_id'] = False
        return res

