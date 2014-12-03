# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Florian da Costa <florian.dacosta@akretion.com>
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
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter

class PrestashopBackend(orm.Model):
    _inherit = 'prestashop.backend'


    def _scheduler_inactive_deleted_record(self, cr, uid, domain=None, context=None):
        if domain is None:
            domain = []
        ids = self.search(cr, uid, domain, context=context)
        session = ConnectorSession(cr, uid, context=context)
        
        for backend_id in ids:
            inactive_record(session, 'prestashop.product.product', backend_id)
            inactive_record(session, 'prestashop.product.combination', backend_id)
        return True

def inactive_record(session, model_name, backend_id):
    obj = session.pool.get(model_name)
    record_ids = obj.search(session.cr, session.uid, [('active', '=', True), ('backend_id', '=', backend_id)])
    dicts = obj.read(session.cr, session.uid, record_ids, ['prestashop_id'])
    ids = map(lambda x: x['prestashop_id'], dicts)
    ids.sort()
    env = get_environment(session, model_name, backend_id)
    adapter = env.get_connector_unit(GenericAdapter)
    print len(record_ids), [min(ids), max(ids)]
    a = 0
    limit = 5000
    while ids[a:limit]:
        to_unactive = []
    #for id in ids:
        filters = {
            'filter[id]': [min(ids[a:limit]),max(ids[a:limit])],
        }
        presta_ids = adapter.search(filters)
        to_unactive = list(set(ids[a:limit]) - set(presta_ids))
        if to_unactive:
            presta_ids = obj.search(session.cr, session.uid, [('prestashop_id', 'in', to_unactive), ('backend_id', '=', backend_id)])
            obj.write(session.cr, session.uid, presta_ids, {'active': False})
        a += 5000
        limit += 5000
    return True



