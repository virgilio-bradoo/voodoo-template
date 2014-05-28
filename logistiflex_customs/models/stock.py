from openerp import netsvc
from openerp.osv.orm import Model
from openerp.osv import fields
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.sale import SaleStateExport
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class StockPicking(Model):
    _inherit = 'stock.picking'

    def _get_order_message_ids(self, cr, uid, ids, field_name, arg,
                               context=None):
        result = {}
        for picking in self.browse(cr, uid, ids, context=context):
            result[picking.id] = []
            if not picking.sale_id or not picking.sale_id.message_ids:
                continue
            for message in picking.sale_id.message_ids:
                if message.prestashop_bind_ids:
                    result[picking.id].append(message.id)
        return result

    _columns = {
        'order_message_ids': fields.function(
            _get_order_message_ids, type='one2many', obj='mail.message',
        ),
    }

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

    def validate(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.state == 'confirmed':
                self.force_assign(cr, uid, [picking.id])
            partial_picking_obj = self.pool.get('stock.partial.picking')
            partial_picking = partial_picking_obj.default_get(
                cr, uid,
                ['picking_id', 'move_ids', 'date'],
                context={
                    'active_ids': [picking.id],
                    'active_model': 'stock.picking',
                }
            )
            partial_picking['move_ids'] = [
                (0, 0, line) for line in partial_picking['move_ids']
            ]
            partial_picking_id = partial_picking_obj.create(
                cr, uid, partial_picking, context=context
            )
            partial_picking_obj.do_partial(
                cr, uid, [partial_picking_id], context=context
            )
        return True

    def action_reopen(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        self.write(cr, uid, ids, {'state': 'draft'})
        pickings = self.read(cr, uid, ids, ['move_lines'], context=context)
        for picking in pickings:
            move_obj.write(
                cr, uid, picking['move_lines'], {'state': 'confirmed'}
            )
            wf_service.trg_delete(uid, 'stock.picking', picking['id'], cr)
            wf_service.trg_create(uid, 'stock.picking', picking['id'], cr)


class StockPickingOut(Model):
    _inherit = 'stock.picking.out'

    def _get_order_message_ids(self, cr, uid, ids, field_name, arg,
                               context=None):
        return self.pool.get('stock.picking')._get_order_messsage_ids(
            cr, uid, ids, field_name, arg, context=context
        )

    _columns = {
        'order_message_ids': fields.function(
            _get_order_message_ids, type='one2many', obj='mail.message',
        ),
    }

    def validate(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').validate(
            cr, uid, ids, context=context
        )


class StockPickingIn(Model):
    _inherit = 'stock.picking.in'

    def validate(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').validate(
            cr, uid, ids, context=context
        )


@job
def export_sale_state(session, prestashop_id, new_state):
    inherit_model = 'prestashop.sale.order'
    sale_order = session.browse('prestashop.sale.order', prestashop_id)
    backend_id = sale_order.backend_id.id
    env = get_environment(session, inherit_model, backend_id)
    sale_exporter = env.get_connector_unit(SaleStateExport)
    sale_exporter.run(sale_order.prestashop_id, new_state)
