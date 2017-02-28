# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2015 Akretion
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
##############################################################################
from openerp.osv import fields, orm
from openerp import SUPERUSER_ID
from openerp.osv.orm import except_orm
import logging

_logger = logging.getLogger(__name__)


class AutomaticDepositWizard(orm.TransientModel):
    _name = "automatic.deposit.wizard"
    _description = "Wizard to create deposit slip automatically"

    def create_automatic_deposit_slip(self, cr, uid, ids, context=None):
        company_obj = self.pool['res.company']
        deposit_wizard_obj = self.pool['delivery.deposit.wizard']
        deposit_obj = self.pool['deposit.slip']
        carrier_types = self.pool['delivery.carrier']._get_carrier_type_selection(
            cr, uid, context=context)
        company_ids = company_obj.search(
            cr, SUPERUSER_ID,
            [('automatic_deposit_slip', '=', True)],
            context=context)
        for company_id in company_ids:
            company_user_id = company_obj.get_company_action_user(
                cr, SUPERUSER_ID, company_id, context=context)
            for carrier_type in carrier_types:
                wizard_id = deposit_wizard_obj.create(
                    cr, company_user_id,
                    {'carrier_type': carrier_type[0]}, context=context)
                try:
                    action = deposit_wizard_obj.create_deposit_slip(
                        cr, company_user_id, [wizard_id], context=context)
                    deposit_id = action['res_id']
                    deposit_obj.validate_deposit(
                        cr, company_user_id, [deposit_id], context=context)
                except except_orm as e:
                    _logger.info(e)
                except Exception as err:
                    raise err
                
