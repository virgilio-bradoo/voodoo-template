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

import hashlib
import requests
from urllib import urlencode
from openerp.addons.connector.queue.job import job

URL = "https://secure-magenta1.be2bill.com/front/service/rest/export.php"

def get_hash(password, params):
    parameters = sorted("{}={}".format(key, value) for key, value in params.items())
    clear_string = password + password.join(parameters) + password
    return hashlib.sha256(clear_string).hexdigest()


@job
def send_file_by_email(session, company_id, date, compression='ZIP', version='2.0'):
    company = session.browse('res.company', company_id)
    login = company.be2bill_login
    password = company.be2bill_password
    email_to = company.be2bill_email_to
    data = build_data(login, password, date, email_to, compression=compression, version=version)
    req = requests.post(URL, data=data)
    print req.text

def build_data(login, password, date, mail, compression, version):
    params = {
        'IDENTIFIER': login,
        'OPERATIONTYPE': 'exportTransactions',
        'DATE': date,
        'COMPRESSION': compression,
        'VERSION': version,
        'MAILTO': mail,
        'TIMEZONE': 'Europe/Paris',
    }
    hash_data = get_hash(password, params)

    data = {
        'method': 'exportTransactions',
        'params[IDENTIFIER]': login,
        'params[OPERATIONTYPE]': 'exportTransactions',
        'params[COMPRESSION]': compression,
        'params[DATE]': date,
        'params[VERSION]': version,
        'params[MAILTO]': mail,
        'params[TIMEZONE]': 'Europe/Paris',
        'params[HASH]': hash_data
    }
    return data



