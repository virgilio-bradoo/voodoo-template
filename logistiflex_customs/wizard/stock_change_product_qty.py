from openerp.osv import osv


class StockChangeProductQty(osv.osv_memory):
    _inherit = "stock.change.product.qty"

    def default_get(self, cr, uid, fields, context):
        res = super(StockChangeProductQty, self).default_get(cr, uid, fields, context)
        if 'location_id' in fields:
            inventory_line_obj = self.pool['stock.inventory.line']
            res['location_id'] = inventory_line_obj._default_stock_location(
                cr, uid, context=context
            )
        return res
