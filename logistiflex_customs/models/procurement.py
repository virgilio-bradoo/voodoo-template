from openerp.osv.orm import Model


class ProcurementOrder(Model):
    _inherit = 'procurement.order'

    def run_scheduler(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        res = super(ProcurementOrder, self).run_scheduler(
                cr, uid, automatic=automatic, use_new_cursor=use_new_cursor,
                context=context)
        self.pool['purchase.order'].check_po_quantities(cr, uid,
                context=context)
        return res
