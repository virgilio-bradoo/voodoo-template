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


class QueueJob(orm.Model):
    _inherit = 'queue.job'

    def create(self, cr, uid, vals, context=None):
        if vals.get('user_id', False):
            user_obj = self.pool['res.users']
            user = user_obj.browse(cr, uid, [vals['user_id']],
                                   context=context)[0]
            if user.company_id.automatic_action_user_id:
                vals['user_id'] = user.company_id.automatic_action_user_id.id
        res = super(QueueJob, self).create(
            cr, uid, vals, context=context)
        return res

