from openerp.osv.orm import Model


class PurchaseOrder(Model):
    _inherit = 'purchase.order'

    def _default_warehouse_id(self, cr, uid, context=None):
        warehouse_obj = self.pool['stock.warehouse']
        warehouse_ids = warehouse_obj.search(cr, uid, [], context=context)
        if not warehouse_ids:
            return None
        return warehouse_ids[0]

    _defaults = {
        'warehouse_id': _default_warehouse_id,
    }

    def _prepare_linked_sale_order(self, cr, uid, po, shop_id, context=None):
        vals = super(PurchaseOrder, self)._prepare_linked_sale_order(
            cr, uid, po, shop_id, context=context
        )
        vals['order_policy'] = 'picking'
        return vals
