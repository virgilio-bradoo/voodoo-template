from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'partial_delivery': fields.boolean('Partial Delivery'),
        'product_geolocation': fields.char('Products Location'),
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(ResPartner, self).write(cr, uid, ids, vals, context=context)
        if vals.get('product_geolocation', False):
            product_obj = self.pool['product.product']
            for partner in self.browse(cr, uid, ids, context=context):
                product_ids = product_obj.search(cr, uid, [('seller_ids', '=', partner.name)])
                product_obj.write(
                        cr, uid, product_ids,
                        {'geolocation': vals.get('product_geolocation')},
                        context=context)
        return res
