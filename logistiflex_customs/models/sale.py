from openerp import SUPERUSER_ID, netsvc
from openerp.osv.orm import Model
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class SaleOrder(Model):
    _inherit = 'sale.order'
    
    # we do not want to merge purchase order which are from produt in "make_to_order" because it is only
    # used for intercompany products and these intercompany purchase order should be validated automatically
#    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
#        res = super(SaleOrder, self)._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context)
#        if line.type == 'make_to_order':
#            res['purchase_auto_merge'] = False
#        return res

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id,
                                 date_planned, context=None):
        res = super(SaleOrder, self)._prepare_order_line_move(
            cr, uid, order, line, picking_id, date_planned, context=context)
        if order.is_intercompany:
            sale_line_obj = self.pool['sale.order.line']
            res['is_intercompany'] = True
            line_id = line.id
            line_admin = sale_line_obj.browse(cr, SUPERUSER_ID, [line.id], context=context)[0]
            move_inter_id = line_admin.purchase_line_id.move_dest_id and line_admin.purchase_line_id.move_dest_id.id
            res['intercompany_move_id'] = move_inter_id
        return res
            
    def action_ship_create(self, cr, uid, ids, context=None):
        result = super(SaleOrder, self).action_ship_create(
            cr, uid, ids, context=None
        )
        self.check_product_orderpoints(cr, uid, ids, context=context)
        po_obj =  self.pool['purchase.order']
        session = ConnectorSession(cr, uid, context=context)
        for sale in self.browse(cr, uid, ids, context=context):
            po_ids = po_obj.search(cr, uid, [('origin', '=', sale.name)], context=context)
            for po in po_obj.browse(cr, uid, po_ids, context=context):
                company = po.partner_id.partner_company_id
                if not company:
                    continue
                po_obj.unlock(cr, uid, [po.id], context=context)
                validate_purchase.delay(session, po.id)
        return result

    def force_action_ship_create(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for sale in self.browse(cr, uid, ids, context=context):
            if sale.workflow_process_id.id == 3:
                sale.write({'workflow_process_id': 1})
                for line in sale.order_line:
                    if line.state != 'draft' and line.product_id.type != 'service':
                        line.write({'state': 'draft'})
        return self.action_ship_create(cr, uid, ids, context=context)

    def check_product_orderpoints(self, cr, uid, ids, context=None):
        product_ids = []
        for sale_order in self.browse(cr, uid, ids, context=context):
            for sale_order_line in sale_order.order_line:
                if sale_order_line.product_id:
                    if sale_order_line.product_id.procure_method == "make_to_stock":
                        product_ids.append(sale_order_line.product_id.id)
        product_obj = self.pool.get('product.product')
        if context is None:
            context = {}
        if product_ids:
            product_obj.check_orderpoints_or_automatic(
                cr, uid, product_ids, context=context
            )
        return True


@job
def validate_purchase(session, purchase_id):
    wf_service = netsvc.LocalService("workflow")
    wf_service.trg_validate(
        session.uid,
        'purchase.order',
        purchase_id,
        'purchase_confirm',
        session.cr
    )

