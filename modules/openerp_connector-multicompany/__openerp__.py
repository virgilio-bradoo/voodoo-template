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

{'name': 'OpenERP Connector Multi-Company',
 'version': '0.0.1',
 'author': 'Akretion',
 'website': 'www.akretion.com',
 'license': 'AGPL-3',
 'category': 'Generic Modules',
 'description': """
    Temporary solution to rule access bug in jobs.
    The problem is : a user can change his company very quickly and the jobs are usually processed every minutes.
    So the case where a user A From company C1 delay a job and then change his company for company C2 just after that.
    The job will try to run but it is linked to the C1 company while his user is linked to company C2.
    The idea is simply to modify the user_id of a job at its creation and replace it by the "automatic" user linked to the company 
    of the original user.
 """,
 'depends': [
     'prestashoperpconnect',
     'multi_company_action_user',
 ],
 'data': [
 ],
 'installable': True,
 'application': False,
}




