# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2014-2015 Akretion
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

"""
Wizard to import product prices by supplier
"""

from openerp.osv import orm, fields


class FileWizard(orm.TransientModel):
    _name = "file.wizard"

    _columns = {
        'file': fields.binary('File', required=True),
        'name': fields.char('File Name', size=128),
        'multifile_wizard_id': fields.many2one('multi.file.wizard', 'Multi Files')
    }

class MultiFileWizard(orm.TransientModel):
    _name = "multi.file.wizard"

    _columns = {
        'file_ids': fields.one2many('file.wizard', 'multifile_wizard_id', 'Files', readonly=True)
    }



