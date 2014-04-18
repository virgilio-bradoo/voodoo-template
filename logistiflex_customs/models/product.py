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


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _update_prestashop_quantities(self, cr, uid, ids, context=None):
        super(ProductProduct, self)._update_prestashop_quantities(
            cr, uid, ids, context=context
        )
        for product in self.browse(cr, uid, ids, context=context):
            for supplierinfo in product.customers_supplierinfo_ids:
                supplierinfo.product_id._update_prestashop_quantities()
