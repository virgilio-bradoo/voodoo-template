from openerp.osv import orm


class PrestashopProductProduct(orm.Model):
    _inherit = 'prestashop.product.product'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return (
            product.suppliers_immediately_usable_qty
            + product.immediately_usable_qty
        )


class PrestashopProductCombination(orm.Model):
    _inherit = 'prestashop.product.combination'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return (
            product.suppliers_immediately_usable_qty
            + product.immediately_usable_qty
        )
