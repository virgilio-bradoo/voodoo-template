from openerp import netsvc, SUPERUSER_ID
from openerp.osv.orm import Model

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job




class SaleOrder(Model):
    _inherit = 'sale.order'

    def action_wait(self, cr, uid, ids, context=None):
        res = super(SaleOrder, self).action_wait(cr, uid, ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        for so_id in ids:
            validate_pickings.delay(session, 'sale.order', so_id)
        return res

    def action_ship_create(self, cr, uid, ids, context=None):
        result = super(SaleOrder, self).action_ship_create(
            cr, uid, ids, context=None
        )
        self.check_product_orderpoints(cr, uid, ids, context=context)
        return result

    def validate_pickings(self, cr, uid, ids, context=None):
        partial_picking_obj = self.pool.get('stock.partial.picking')
        for sale_order in self.browse(cr, SUPERUSER_ID, ids, context=context):
            for picking in sale_order.picking_ids:
                picking.validate()
            if sale_order.purchase_id:
                for picking in sale_order.purchase_id.picking_ids:
                    picking.validate()
        return True

    def check_product_orderpoints(self, cr, uid, ids, context=None):
        product_ids = []
        for sale_order in self.browse(cr, uid, ids, context=context):
            for sale_order_line in sale_order.order_line:
                if sale_order_line.product_id:
                    product_ids.append(sale_order_line.product_id.id)
        product_obj = self.pool.get('product.product')
        product_obj.create_automatic_op(cr, uid, product_ids, context=context)
        product_obj.check_orderpoints(cr, uid, product_ids, context=context)


@job
def validate_pickings(session, model_name, ps_sale_order_id):
    session.pool.get(model_name).validate_pickings(
        session.cr, session.uid, [ps_sale_order_id], session.context
    )
