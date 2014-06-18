from openerp.osv.orm import Model
from openerp.osv import fields


class MrpBom(Model):
    _inherit = 'mrp.bom'

    _columns = {
        'name': fields.related(
            'product_id', 'name', type='char', string='Name'
        ),
    }
