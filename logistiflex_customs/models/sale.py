from openerp import SUPERUSER_ID, netsvc
from openerp.osv.orm import Model

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class SaleOrder(Model):
    _inherit = 'sale.order'

    def action_wait(self, cr, uid, ids, context=None):
        res = super(SaleOrder, self).action_wait(cr, uid, ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        for sale_order in self.browse(cr, uid, ids, context=context):
            if not sale_order.is_intercompany:
                continue
            validate_pickings.delay(session, 'sale.order', sale_order.id)
        return res

    def action_ship_create(self, cr, uid, ids, context=None):
        result = super(SaleOrder, self).action_ship_create(
            cr, uid, ids, context=None
        )
        self.check_product_orderpoints(cr, uid, ids, context=context)
        return result

    def validate_pickings(self, cr, uid, ids, context=None):
        for sale_order in self.browse(cr, SUPERUSER_ID, ids, context=context):
            if not sale_order.is_intercompany:
                continue
            for picking in sale_order.picking_ids:
                picking.validate()
            if sale_order.purchase_id:
                for picking in sale_order.purchase_id.picking_ids:
                    picking.validate()
        return True

    def check_product_orderpoints(self, cr, uid, ids, context=None):
        product_ids_to_validate = []
        product_ids = []
        for sale_order in self.browse(cr, uid, ids, context=context):
            for sale_order_line in sale_order.order_line:
                if sale_order_line.product_id:
                    if sale_order_line.product_id.has_same_erp_supplier:
                        product_ids_to_validate.append(
                            sale_order_line.product_id.id
                        )
                    else:
                        product_ids.append(sale_order_line.product_id.id)
        product_obj = self.pool.get('product.product')
        if context is None:
            context = {}
        product_obj.create_automatic_op(
            cr, uid, product_ids, context=context
        )
        product_obj.check_orderpoints(
            cr, uid, product_ids, context=context
        )
        context['purchase_auto_merge'] = False
        proc_ids = []
        proc_ids += product_obj.create_automatic_op(
            cr, uid, product_ids_to_validate, context=context
        )
        proc_ids += product_obj.check_orderpoints(
            cr, uid, product_ids_to_validate, context=context
        )
        for proc_id in proc_ids:
            session = ConnectorSession(cr, uid, context=context)
            validate_procurement_purchase.delay(session, proc_id)


@job
def validate_pickings(session, model_name, ps_sale_order_id):
    session.pool.get(model_name).validate_pickings(
        session.cr, session.uid, [ps_sale_order_id], session.context
    )


@job
def validate_procurement_purchase(session, proc_id):
    proc_obj = session.pool.get('procurement.order')
    proc = proc_obj.browse(session.cr, session.uid, proc_id, session.context)
    wf_service = netsvc.LocalService("workflow")
    wf_service.trg_validate(
        session.uid,
        'purchase.order',
        proc.purchase_id.id,
        'purchase_confirm',
        session.cr
    )
