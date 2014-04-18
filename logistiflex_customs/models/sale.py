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

    def validate_purchase(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for ps_so in self.browse(cr, uid, ids, context=context):
            for order_line in ps_so.order_line:
                if not(order_line.product_id and order_line.product_id.has_same_erp_supplier()):
                    continue
                for move_id in order_line.move_ids:
                    for procurement in move_id.procurements:
                        if procurement.purchase_id:
                            wf_service.trg_validate(uid, 'purchase.order', procurement.purchase_id.id, 'purchase_confirm', cr)


@job
def validate_purchase(session, model_name, ps_sale_order_id):
    session.pool.get(model_name).validate_purchase(
        session.cr, session.uid, [ps_sale_order_id], session.context
    )
