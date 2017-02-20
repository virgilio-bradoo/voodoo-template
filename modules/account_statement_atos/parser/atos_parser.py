#-*- coding: utf-8 -*-
###############################################################################
#
#   account_statement_bnp_import for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#            Benoît Guillot <benoit.guillot@akretion.com>
#   Copyright 2013 Akretion
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

from openerp.tools.translate import _
import datetime
from account_statement_base_import.parser.file_parser import FileParser
from csv import Dialect
from _csv import QUOTE_MINIMAL, register_dialect
from openerp.osv import osv 

def float_or_zero(val):
    """ Conversion function used to manage
    empty string into float usecase"""
    val = val.strip()
    return (float(val.replace(',', '.')) if val else 0.0) / 100.

def format_date(val):
    return datetime.datetime.strptime(val, "%Y%m%d")

class atos_dialect(Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = '\t'
    quotechar = '"'
    doublequote = False
    skipinitialspace = False
    lineterminator = '\n'
    quoting = QUOTE_MINIMAL
register_dialect("atos_dialect", atos_dialect)


class AtosFileParser(FileParser):
    """
    Standard parser that use a define format in csv or xls to import into a
    bank statement. This is mostely an example of how to proceed to create a new
    parser, but will also be useful as it allow to import a basic flat file.
    """

    def __init__(self, parse_name, ftype='csv'):
        conversion_dict = {
            "OPERATION_DATE": format_date,
            "PAYMENT_DATE": format_date,
            "TRANSACTION_ID": unicode,
            "OPERATION_NAME": unicode,
            "OPERATION_AMOUNT": float_or_zero,
            "OPERATION_SEQUENCE": unicode,
        }
        self.refund_amount = None
        super(AtosFileParser,self).__init__(parse_name, ftype=ftype,
                                           conversion_dict=conversion_dict,
                                           dialect=atos_dialect)

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is generic_csvxls_so
        """
        return parser_name == 'atos_csvparser'

    def _pre(self, *args, **kwargs):
        split_file = self.filebuffer.split("\n")
        selected_lines = []
        for line in split_file:
            if line.startswith("FIN"):
                break
            selected_lines.append(line.strip())
        self.filebuffer = "\n".join(selected_lines)

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the responsibility
        of every parser to give this dict of vals, so each one can implement his
        own way of recording the lines.
            :param:  line: a dict of vals that represent a line of result_row_list
            :return: dict of values to give to the create method of statement line,
                     it MUST contain at least:
                {
                    'name':value,
                    'date':value,
                    'amount':value,
                    'ref':value,
                    'label':value,
                    'commission_amount':value,
                }
        In this generic parser, the commission is given for every line, so we store it
        for each one.
        """

        res = {
            'name': line["TRANSACTION_ID"],
            'date': line["OPERATION_DATE"],
            'amount': line['OPERATION_AMOUNT'],
            'ref': '/',
            'transaction_id': line["TRANSACTION_ID"],
            'label': line["OPERATION_NAME"],
            'atos_payment_sequence': line["OPERATION_SEQUENCE"],
            'atos_payment_date': line["PAYMENT_DATE"],
        }
        return res

    def _post(self, *args, **kwargs):
        """
        Compute the total transfer amount
        """
        res = super(AtosFileParser, self)._post(*args, **kwargs)
        self.transfer_amount = 0.0
        self.refund_amount = 0.0
        rows = []
        for row in self.result_row_list:
            if row['OPERATION_NAME'] in ('CREDIT', 'AUTHOR', 'CANCEL'):
               continue
            rows.append(row)
            if row['OPERATION_NAME'] == 'CREDIT_CAPTURE':
                row["OPERATION_AMOUNT"] = - row["OPERATION_AMOUNT"]
                self.refund_amount -= row["OPERATION_AMOUNT"]
            elif row['OPERATION_NAME'] == 'DEBIT_CAPTURE':
                self.transfer_amount -= row["OPERATION_AMOUNT"]
            else:
                raise osv.except_osv(_("User Error"),
                    _("The bank statement imported have invalide line,"
                    " indeed the operation type %s is not supported"
                    )%row['OPERATION_NAME'])
        self.result_row_list = rows
        if self.result_row_list:
            self.statement_date = self.result_row_list[0]["OPERATION_DATE"]
        return res

    def get_refund_amount(self):
        return self.refund_amount
