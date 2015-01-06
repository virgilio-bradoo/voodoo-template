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
from datetime import datetime, timedelta


class QueueJob(orm.Model):
    _inherit = 'queue.job'

    def check_last_job_done(self, cr, uid, delay=False, context=None):
        last_job_done_ids = self.search(cr, uid, [('state', '=', 'done'), ('date_done', '!=', False)], limit=1, order='date_done desc')
        last_job = self.browse(cr, uid, last_job_done_ids, context=context)[0]
        last_date = last_job.date_done
        last_date = datetime.strptime(last_date, '%Y-%m-%d %H:%M:%S')
        now = datetime.today()
        diff = now - last_date
        if not delay:
            delay = 2
        max_delay = timedelta(hours=delay)
        print max_delay, "jj", diff
        if max_delay > diff:
            tmpl_obj = self.pool['email.template']
            template_id = tmpl_obj.search(cr, uid, [('name', '=', 'Check Queue Job')], context=context)[0]
            tmpl_obj.send_mail(cr, uid, template_id, last_job.id, force_send=True, context=context)
        return True

