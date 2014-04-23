from openerp.osv.orm import Model
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.sale import SaleStateExport
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class StockPicking(Model):
    _inherit = 'stock.picking'

    def action_done(self, cr, uid, ids, context=None):
        result = super(StockPicking, self).action_done(
            cr, uid, ids, context=context
        )
        session = ConnectorSession(cr, uid, context=context)
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type != 'out' or not picking.sale_id:
                continue
            for ps_sale in picking.sale_id.prestashop_bind_ids:
                if not ps_sale.backend_id.shipping_state_id:
                    continue
                export_sale_state.delay(
                    session,
                    ps_sale.id,
                    ps_sale.backend_id.shipping_state_id.prestashop_id
                )

        return result


@job
def export_sale_state(session, prestashop_id, new_state):
    inherit_model = 'prestashop.sale.order'
    sale_order = session.browse('prestashop.sale.order', prestashop_id)
    backend_id = sale_order.backend_id.id
    env = get_environment(session, inherit_model, backend_id)
    sale_exporter = env.get_connector_unit(SaleStateExport)
    sale_exporter.run(sale_order.id, new_state)
