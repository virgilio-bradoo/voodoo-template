# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author David BEAL <david.beal@akretion.com>
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
###############################################################################

{
    'name': 'Delivery Carrier File Document',
    'version': '0.1',
    'author': 'Akretion',
    'summary': "Glue module between carrier delivery and file document",
    'maintener': 'Akretion',
    'category': 'Warehouse',
    'depends': [
        'base_delivery_carrier_label',
        'file_document',
    ],
    'description': """
Delivery Carrier Akretion
===========================


Contributors

------------

* David BEAL <david.beal@akretion.com>

""",
    'website': 'http://www.akretion.com/',
    'data': [
        'stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'AGPL-3',
    'external_dependencies': {
        'python': [],
    },
    'tests': [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
