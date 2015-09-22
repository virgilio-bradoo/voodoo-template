from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'partial_delivery': fields.boolean('Partial Delivery')
    }
