# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   multi_company_supplier for OpenERP                                        #
#   Copyright (C) 2014 Akretion Florian da Costa <florian.dacosta@akretion.com>#
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
{
    'name': 'Stock Inventory Check Move Assignment',
    'version': '1',
    'category': 'Client',
    'description': """
When updating the stock level of a product, check the stock move of the same product to check if it should change state.
""" ,
    'author': 'Florian da Costa',
    'website': 'http://www.akretion.com',
    'depends': [
        'stock',
    ],
    'data': [
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
