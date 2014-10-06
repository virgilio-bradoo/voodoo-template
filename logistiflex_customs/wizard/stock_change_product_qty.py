from openerp.osv import osv
from openerp import SUPERUSER_ID


class StockChangeProductQty(osv.osv_memory):
    _inherit = "stock.change.product.qty"

#    def change_product_qty(self, cr, uid, ids, context=None):
#        if context is None:
#            context = {}
#
#        rec_id = context and context.get('active_id', False)
#        supplierinfo_obj = self.pool['product.supplierinfo']
#        prod_obj = self.pool['product.product']
#        supplier_ids = supplierinfo_obj.search(cr, SUPERUSER_ID, [('supplier_product_id', '=', rec_id)])
#        #tot = prod_obj.read(cr, uid, [rec_id], ['qty_available'])[0]['qty_available']
#        tot = 0.0
#            
#        if supplier_ids:
#            supp_read = supplierinfo_obj.read(cr, SUPERUSER_ID, supplier_ids, ['product_id'])
#            prod_ids = [supp['product_id'][0] for supp in supp_read if supp['product_id']]
#            for prod_id in prod_ids:
#                new_uid = prod_obj.get_record_id_user(cr, uid, prod_id,
#                                                      context=context)
#                tot += prod_obj.read(cr, new_uid, [prod_id], ['qty_available'])[0]['qty_available']
#        if tot:
#            for data in self.browse(cr, uid, ids, context=context):
#                if data.new_quantity < 0:
#                    raise osv.except_osv(_('Warning!'), _('Quantity cannot be negative.'))
#                new_qty = data.new_quantity - tot
#                self.write(cr, uid, ids, {'new_quantity': new_qty})
#        res = super(StockChangeProductQty, self).change_product_qty(cr, uid, ids, context)
#        return res

    def default_get(self, cr, uid, fields, context):
        res = super(StockChangeProductQty, self).default_get(cr, uid, fields, context)
        if 'location_id' in fields:
            inventory_line_obj = self.pool['stock.inventory.line']
            res['location_id'] = inventory_line_obj._default_stock_location(
                cr, uid, context=context
            )
        return res
