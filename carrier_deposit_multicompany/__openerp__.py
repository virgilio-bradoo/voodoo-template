# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Akretion (<http://www.akretion.com>).
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

{'name': 'Carrier Deposit Multi-Company',
 'version': '0.2',
 'author': 'Akretion',
 'website': 'http://www.akretion.com',
 'license': 'AGPL-3',
 'category': 'Warehouse',
 'summary': 'Allows to generate deposit slip for all carrier type and all company at one time.',
 'depends': ['delivery_carrier_deposit',
             'multi_company_action_user',
             ],
 'data': [
          'security/security.xml',
          'company_view.xml',
          'wizard/automatic_deposit_view.xml',
          ],
 'installable': True,
 }
