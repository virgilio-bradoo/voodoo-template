from openerp.osv.orm import Model


class PurchaseOrder(Model):
    _inherit = 'purchase.order'

    def _prepare_linked_sale_order(self, cr, uid, po, shop_id, context=None):
        vals = super(PurchaseOrder, self)._prepare_linked_sale_order(
            cr, uid, po, shop_id, context=context
        )
        vals['order_policy'] = 'picking'
        return vals
