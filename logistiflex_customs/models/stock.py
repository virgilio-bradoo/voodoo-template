from openerp import SUPERUSER_ID, netsvc
from openerp.osv.orm import Model, TransientModel
from openerp.osv import fields
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.sale import SaleStateExport
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


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
        # note evenif we need a one2many we use a many2many
        # because function field in one2many are broken
        'order_message_ids': fields.function(
            _get_order_message_ids, type='many2many', obj='mail.message',
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
            _get_order_message_ids, type='many2many', obj='mail.message',
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


class StockMove(Model):
    _inherit = 'stock.move'

    _columns = {
        'bom_id': fields.many2one('mrp.bom', 'Pack'),
        'is_intercompany': fields.boolean('Is Intercompany'),
        'intercompany_move_id': fields.many2one('stock.move', 'Intercomany Move'),
    }


    def write(self, cr, uid, ids, vals, context=None):
        if (vals.get('state', False) and 
                vals['state'] in ('assigned', 'confirmed')):
            wf_service = netsvc.LocalService("workflow")
            for move_read in self.read(cr, uid, ids, ['is_intercompany'],
                                       context=context):
                if move_read['is_intercompany']:
                    print move_read
                    move_super = self.read(cr, SUPERUSER_ID, 
                                             [move_read['id']], 
                                             ['intercompany_move_id'])[0]
                    move_dest_id = move_super['intercompany_move_id'][0]
                    new_uid = self.get_record_id_user(cr, uid, move_dest_id,
                                                      context=context)
                    print "????", new_uid, "!!", move_dest_id
                    self.write(cr, new_uid, [move_dest_id],
                               {'state': vals['state']})
                    move_dest = self.browse(cr, new_uid,
                                            [move_dest_id],
                                            context=context)[0]
                    if move_dest.picking_id:
                        wf_service.trg_write(new_uid, 'stock.picking',
                                             move_dest.picking_id.id, cr)
        return  super(StockMove, self).write(cr, uid, ids, vals,
                                             context=context)
                

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(StockMove, self).action_cancel(cr, uid, ids, context=context)
        intercompany_linked_move_ids = self.search(cr, SUPERUSER_ID, [
                                       ('is_intercompany', '=', True),
                                       ('intercompany_move_id', 'in', ids),])
        print "****", intercompany_linked_move_ids
        for linked_move_id in intercompany_linked_move_ids:
            new_uid = self.get_record_id_user(cr, uid, linked_move_id,
                                              context=context)
            self.action_cancel(cr, new_uid, [linked_move_id], context=context)
        return True

    def _action_explode(self, cr, uid, move, context=None):
        move_ids = super(StockMove, self)._action_explode(
            cr, uid, move, context=context
        )
        bom_obj = self.pool.get('mrp.bom')
        for move in self.browse(cr, uid, move_ids, context=context):
            if not move.sale_line_id or not move.sale_line_id.product_id:
                continue
            product_id = move.sale_line_id.product_id.id
            if move.product_id.id == product_id:
                continue
            bom_ids = bom_obj.search(cr, uid, [
                ('product_id', '=', product_id),
                ('bom_id', '=', False),
                ('type', '=', 'phantom')
            ])
            if not bom_ids:
                continue
            move.write({'bom_id': bom_ids[0]})
        return move_ids

class StockPartialPicking(TransientModel):
    _inherit = 'stock.partial.picking'



    def update_move_pick_dict(self, cr, uid, move_id, pick_move_dict, context=None):
        move_obj = self.pool['stock.move']
        move_read = move_obj.read(cr, uid, [move_id],
                                  ['picking_id'], context=context)[0]
        picking_id = move_read['picking_id'][0]
        if pick_move_dict.get(picking_id, False):
            pick_move_dict[picking_id] += [move_id]
        else:
            pick_move_dict[picking_id] = [move_id]
        return pick_move_dict

    def validate_moves_from_dict(self, cr, uid, pick_move_dict, context=None):
        move_obj = self.pool['stock.move']
        for p, move_ids in pick_move_dict.iteritems():
            new_uid = move_obj.get_record_id_user(cr, uid, move_ids[0], context=context)
            moves = move_obj.browse(cr, new_uid, move_ids, context=context)
            partial_vals = {
                'picking_id': p,
                'move_ids': [(0, 0, self._partial_move_for(cr, new_uid, m)) for m in moves if m.state not in ('done','cancel')],
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            }
            partial_picking_id = self.create(cr, new_uid, partial_vals,
                                             context=context)
            self.do_partial(cr, new_uid, [partial_picking_id], context=context)
        return True

    def do_partial(self, cr, uid, ids, context=None):
        res = super(StockPartialPicking, self).do_partial(
                cr, uid, ids, context=context)
        partial = self.browse(cr, uid, ids[0], context=context)
        intercompany_move_dict = {}
        move_in_dict = {}
        move_obj = self.pool['stock.move']
        for wizard_line in partial.move_ids:
            move_id = wizard_line.move_id.id
            if not wizard_line.quantity:
                continue
            intercompany_move_ids = move_obj.search(cr, SUPERUSER_ID, [
                                      ('is_intercompany', '=', True),
                                      ('intercompany_move_id', '=', move_id)])
            move_in_ids = move_obj.search(cr, SUPERUSER_ID, [
                                      ('picking_id.type', '=', 'in'),
                                      ('move_dest_id', '=', move_id),
                                      ('state', '=', 'assigned')])
            print "kkkkkkkkkkkkkkkkkkkkkkkk", intercompany_move_ids, "jj", len(intercompany_move_ids)

            assert len(intercompany_move_ids) <= 1, 'More than one intercompany move found for move_id %s' % (move_id)
            assert len(move_in_ids) <= 1, 'More than one reception move found for move_id %s' % (move_id)

            if intercompany_move_ids:
                intercompany_move_dict = self.update_move_pick_dict(cr,
                                            SUPERUSER_ID,
                                            intercompany_move_ids[0], 
                                            intercompany_move_dict, 
                                            context=context)
            if move_in_ids:
                move_in_dict = self.update_move_pick_dict(cr,
                                            SUPERUSER_ID,
                                            move_in_ids[0], 
                                            move_in_dict, 
                                            context=context)
        if intercompany_move_dict:
            self.validate_moves_from_dict(cr, uid, intercompany_move_dict, context=context)
        if move_in_dict:
            self.validate_moves_from_dict(cr, uid, move_in_dict, context=context)
        return res
            

        

class StockInventoryLine(Model):
    _inherit = 'stock.inventory.line'

    def _default_stock_location(self, cr, uid, context=None):
        warehouse_obj = self.pool['stock.warehouse']
        warehouse_ids = warehouse_obj.search(cr, uid, [], context=context)
        if not warehouse_ids:
            return super(StockInventoryLine, self)._default_stock_location(
                cr, uid, context=context
            )
        warehouse = warehouse_obj.browse(cr, uid, warehouse_ids[0], context=context)
        return warehouse.lot_stock_id.id

    _defaults = {
        'location_id': _default_stock_location
    }



@job
def export_sale_state(session, prestashop_id, new_state):
    inherit_model = 'prestashop.sale.order'
    sale_order = session.browse('prestashop.sale.order', prestashop_id)
    backend_id = sale_order.backend_id.id
    env = get_environment(session, inherit_model, backend_id)
    sale_exporter = env.get_connector_unit(SaleStateExport)
    sale_exporter.run(sale_order.prestashop_id, new_state)
