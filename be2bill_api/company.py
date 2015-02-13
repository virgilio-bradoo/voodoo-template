# -*- coding: utf-8 -*-
###############################################################################
#
#   account_statement_be2bill for OpenERP
#   Copyright (C) 2014-TODAY Akretion <http://www.akretion.com>.
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
from .webservice import send_file_by_email
from openerp.addons.connector.session import ConnectorSession
import datetime
from datetime import timedelta


class ResCompany(orm.Model):
    _inherit = "res.company"

    _columns = {
        'be2bill_login': fields.char('Be2Bill Login'),
        'be2bill_password': fields.char('Be2Bill Password'),
        'be2bill_email_to': fields.char('Be2Bill Email TO'),
    }

    def _scheduler_be2bill_get_file(self, cr, uid, context=None):
        session = ConnectorSession(cr, uid, context=context)
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        company_ids = self.search(cr, uid, [('id', '=', user.company_id.id)], context=context)
        for company_id in company_ids:
            yesterday = datetime.date.today() - timedelta(days=1)
            date = yesterday.isoformat()
            send_file_by_email.delay(session, company_id, date)
        return True

    def get_file_manually(self, cr, uid, date, context=None):
        session = ConnectorSession(cr, uid, context=context)
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        company_ids = self.search(cr, uid, [('id', '=', user.company_id.id)], context=context)
        for company_id in company_ids:
            send_file_by_email(session, company_id, date)
        return True


