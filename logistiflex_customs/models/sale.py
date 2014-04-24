from openerp import netsvc
from openerp.osv.orm import Model

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class SaleOrder(Model):
    _inherit = 'sale.order'

    def action_wait(self, cr, uid, ids, context=None):
        res = super(SaleOrder, self).action_wait(cr, uid, ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        for so_id in ids:
            validate_purchase.delay(session, 'sale.order', so_id)
        return res

    def action_ship_create(self, cr, uid, ids, context=None):
        result = super(SaleOrder, self).action_ship_create(
            cr, uid, ids, context=None
        )
        self.check_product_orderpoints(cr, uid, ids, context=context)
        return result

    def validate_purchase(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for ps_so in self.browse(cr, uid, ids, context=context):
            for order_line in ps_so.order_line:
                if not(order_line.product_id and
                        order_line.product_id.has_same_erp_supplier()):
                    continue
                for move_id in order_line.move_ids:
                    for procurement in move_id.procurements:
                        if procurement.purchase_id:
                            wf_service.trg_validate(
                                uid,
                                'purchase.order',
                                procurement.purchase_id.id,
                                'purchase_confirm',
                                cr
                            )

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
def validate_purchase(session, model_name, ps_sale_order_id):
    session.pool.get(model_name).validate_purchase(
        session.cr, session.uid, [ps_sale_order_id], session.context
    )
