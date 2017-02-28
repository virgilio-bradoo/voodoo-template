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

    def update_po_quantities(self, cr, uid, ids, context=None):
        proc_obj = self.pool['procurement.order']
        for po in self.browse(cr, uid, ids, context=context):
            if po.state != 'draft' or not po.lock:
                continue
#            product_qties = {}
            for line in po.order_line:
                if not line.product_id:
                    continue
                product = line.product_id
                if not (product.procure_method == 'make_to_stock' and
                        product.supply_method == 'buy'):
                    continue
#                diff = 0.0
#                if product_qties.get(product.id, False):
#                    product_qties[product.id] += line.product_qty
#                else:
#                    product_qties[product.id] = line.product_qty or 0.0
                if product.virtual_available <= 0:
                    continue
                #Carefule regle de stock avec min??? normal d'avoir du virtual qty
                diff = product.virtual_available
                orderpoint_ids = self.pool['stock.warehouse.orderpoint'].search(
                        cr, uid,
                        [('product_id', '=', product.id),   
                         ('company_id', '=', po.company_id.id)],
                        context=context)
                if orderpoint_ids:
                    continue
                if diff >= line.product_qty:
                    line.unlink()
                else:
                    for proc in line.procurement_ids:
                        if proc.product_qty <= diff:
                            proc.action_cancel()
                            diff -= proc.product_qty
                        else:
                            rest = proc.product_qty - diff
                            proc.write({'product_qty': rest})
                            proc.move_id.write({'product_qty': rest})
                            line.write({'product_qty': line.product_qty - diff})
        return True

    def check_po_quantities(self, cr, uid, context=None):
        po_ids = self.search(cr, uid,
                             [('state', '=', 'draft'), ('lock', '=', True)],
                             context=context)
        self.update_po_quantities(cr, uid, po_ids, context=context)
        return True
                        

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
