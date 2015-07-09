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

    # Sometimes a intercompany product is not linked to its supplier's product
    # In this case, the procure method is make to stock and the purchase order
    # won't validate. We do not want to merge a make to order intercompany purchase
    # with it
    def _get_existing_purchase_order(self, cr, uid, po_vals, context=None):
        res = super(PurchaseOrder, self)._get_existing_purchase_order(
            cr, uid, po_vals, context=context
        )
        if res:
            po = self.browse(cr, uid, res, context=context)
            if po.partner_id.partner_company_id:
                return False
        return res

class PurchaseOrderLine(Model):
    _inherit = 'purchase.order.line'

    def _get_existing_purchase_order_line(self, cr, uid, po_line_vals,
                                          context=None):
        res = super(PurchaseOrderLine, self)._get_existing_purchase_order_line(
            cr, uid, po_line_vals, context=context
        )
        if res:
            po_line = self.browse(cr, uid, res, context=context)
            if po_line.product_id:
                for supplier in po_line.product_id.seller_ids:
                    if supplier.supplier_product_id:
                        return False
        return res
