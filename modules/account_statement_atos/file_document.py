# -*- coding: utf-8 -*-
###############################################################################
#
#   account_statement_atos for OpenERP
#   Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
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

from openerp.osv import orm, fields, osv
import base64
import unicodecsv
from cStringIO import StringIO
import base64
from openerp.tools.translate import _
import logging


SUBJECT_TO_PROCESS = [
#    u'liste des paiements trait\xe9s',
    u"liste des operations effectu\xe9es",
]

EMAIL_FROM = u"so_send_journal_fond@sips-atos.com" 

_logger = logging.getLogger(__name__)

class file_document(orm.Model):
    _inherit = "file.document"

    def get_file_document_type(self, cr, uid, context=None):
        res = super(file_document, self).get_file_document_type(cr, uid, context=context)
        res.append(('atos_transaction', 'Atos Transaction'))
        return res

    def _prepare_data_for_file_document(self, cr, uid, msg, context=None):
        res = super(file_document, self).\
                _prepare_data_for_file_document(cr, uid, msg, context=context)
        if msg['from'] == EMAIL_FROM and msg['subject'] in SUBJECT_TO_PROCESS and res:
            file_name = res[0].get('datas_fname', False)
            if file_name:
                res[0]['datas_fname'] = file_name.replace('.xls', '.csv')
        _logger.info('file document datas : %s', res)
        return res

    def is_empty(self, cr, uid, filedocument, context=None):
        if filedocument.file_type == 'bank_statement'\
                and filedocument.profile_id.import_type == 'atos_csvparser':
            lines = base64.b64decode(filedocument.datas).split('\r\n')
            if len(lines) <= 2:
                _logger.info('The file document with the id %s is empty, skip the import'%filedocument.id)
                return True
        return False

    def _run(self, cr, uid, filedocument, context=None):
        super(file_document, self)._run(cr, uid, filedocument, context=context) 
        if filedocument.file_type == 'atos_transaction':
            sale_obj = self.pool['sale.order']
            lines = base64.b64decode(filedocument.datas).split('\r\n')
            lines = [line.strip() for line in lines[1:]]
            f = StringIO()
            f.write('\n'.join(lines))
            f.seek(0)
            error=""
            for line in unicodecsv.DictReader(f, delimiter="\t", encoding='utf-8'):
                sale_id = sale_obj.search(cr, uid, [
                                ['name', 'ilike', line['ORDER_ID']],
                                ], context=context)
                if not sale_id and line['TRANSACTION_STATUS'] != u'REFUSED':
                    error += _("There is no order %s\n")%line['ORDER_ID']
                sale_obj.write(cr, uid, sale_id, {
                        'transaction_id': line['PAYMENT_DATE'] + line['TRANSACTION_ID'],
                        },context=context)
            if error:
                raise Exception(error)

