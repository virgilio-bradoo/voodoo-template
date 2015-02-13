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
import zipfile
import tempfile

class FileDocument(orm.Model):
    _inherit = "file.document"


    def _prepare_data_for_file_document(self, cr, uid, msg, context=None):
        if msg.get('attachments', False):
            new_attachments = []
            for att in msg.get('attachments'):
                if att[0].split('.')[-1] == 'zip':
                    temp = tempfile.TemporaryFile('w+b', -1, '.zip')
                    temp.write(att[1])
                    temp.seek(0)
                    my_file = zipfile.ZipFile(temp, 'r')
                    new_name = my_file.namelist()[0]
                    new_datas = my_file.read(new_name).strip()
                    new_att = (new_name, new_datas)
                    new_attachments.append(new_att)
                else:
                    new_attachments.append(att)
            msg['attachments'] = new_attachments

        res = super(FileDocument, self)._prepare_data_for_file_document(
            cr, uid, msg, context=context)
        return res

