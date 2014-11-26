from openerp import netsvc
from openerp.osv import orm


class PrestashopProductProduct(orm.Model):
    _inherit = 'prestashop.product.product'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return (
            product.suppliers_immediately_usable_qty
            + product.immediately_usable_qty
        )


class PrestashopProductCombination(orm.Model):
    _inherit = 'prestashop.product.combination'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return (
            product.suppliers_immediately_usable_qty
            + product.immediately_usable_qty
        )


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def update_prestashop_quantities(self, cr, uid, ids, context=None):
        super(ProductProduct, self).update_prestashop_quantities(
            cr, uid, ids, context=context
        )
        for product in self.browse(cr, uid, ids, context=context):
            for supplierinfo in product.customers_supplierinfo_ids:
                supplierinfo.product_id.update_prestashop_quantities()
        return True

    #fill purchase description with product name on creation(only on creation)
    def create(self, cr, uid, vals, context=None):
        if vals.get('name', False) and not vals.get('description_purchase', False):
            vals['description_purchase'] = vals.get('name')
        return super(ProductProduct, self
                     ).create(cr, uid, vals, context=context)

    def create_automatic_op(self, cr, uid, product_ids, context=None):
        if context is None:
            context = {}
        proc_obj = self.pool.get('procurement.order')
        warehouse_obj = self.pool.get('stock.warehouse')
        wf_service = netsvc.LocalService("workflow")

        warehouse_ids = warehouse_obj.search(cr, uid, [], context=context)
        warehouses = warehouse_obj.browse(
            cr, uid, warehouse_ids, context=context
        )
        proc_ids = []
        for warehouse in warehouses:
            context['warehouse'] = warehouse
            products = self.read(
                cr, uid, product_ids, ['virtual_available'], context=context
            )
            for product_read in products:
                if product_read['virtual_available'] >= 0.0:
                    continue

                product = self.browse(
                    cr, uid, product_read['id'], context=context
                )
                if product.supply_method == 'buy':
                    location_id = warehouse.lot_input_id.id
                elif product.supply_method == 'produce':
                    location_id = warehouse.lot_stock_id.id
                else:
                    continue
                proc_vals = proc_obj._prepare_automatic_op_procurement(
                    cr, uid, product, warehouse, location_id, context=context
                )
                proc_vals['purchase_auto_merge'] = context.get(
                    'purchase_auto_merge', True
                )
                proc_id = proc_obj.create(cr, uid, proc_vals, context=context)
                proc_ids.append(proc_id)
                wf_service.trg_validate(
                    uid, 'procurement.order', proc_id, 'button_confirm', cr
                )
                wf_service.trg_validate(
                    uid, 'procurement.order', proc_id, 'button_check', cr
                )
        return proc_ids

    def get_orderpoint_ids(self, cr, uid, product_ids, context=None):
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        return orderpoint_obj.search(
            cr, uid,
            [
                ('product_id', 'in', product_ids),
                ('active', '=', True)
            ],
            context=context
        )

    def check_orderpoints_or_automatic(self, cr, uid, product_ids,
                                       context=None):
        proc_ids = []
        for product_id in product_ids:
            op_ids = self.get_orderpoint_ids(
                cr, uid, [product_id], context=context
            )
            if not op_ids:
                proc_ids += self.create_automatic_op(
                    cr, uid, [product_id], context=context
                )
            else:
                proc_ids += self.check_orderpoints(
                    cr, uid, [product_id], context=context
                )
        return proc_ids

    def check_orderpoints(self, cr, uid, product_ids, context=None):
        if context is None:
            context = {}
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        op_ids = self.get_orderpoint_ids(cr, uid, product_ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        proc_ids = []
        for op in orderpoint_obj.browse(cr, uid, op_ids, context=context):
            prods = proc_obj._product_virtual_get(cr, uid, op)
            if prods is None or prods >= op.product_min_qty:
                continue

            qty = max(op.product_min_qty, op.product_max_qty)-prods

            reste = qty % op.qty_multiple
            if reste != 0:
                if op.product_max_qty:
                    qty -= reste
                else:
                    qty += op.qty_multiple - reste

            if qty <= 0:
                continue
            if op.product_id.type != 'consu' and op.procurement_draft_ids:
                # Check draft procurement related to this order point
                pro_ids = [x.id for x in op.procurement_draft_ids]
                procure_datas = proc_obj.read(
                    cr, uid, pro_ids, ['id', 'product_qty'], context=context
                )
                to_generate = qty
                for proc_data in procure_datas:
                    if to_generate >= proc_data['product_qty']:
                        wf_service.trg_validate(
                            uid,
                            'procurement.order',
                            proc_data['id'],
                            'button_confirm',
                            cr
                        )
                        proc_obj.write(
                            cr, uid,
                            [proc_data['id']],
                            {'origin': op.name},
                            context=context
                        )
                        to_generate -= proc_data['product_qty']
                    if not to_generate:
                        break
                qty = to_generate

            if qty:
                proc_vals = proc_obj._prepare_orderpoint_procurement(
                    cr, uid, op, qty, context=context
                )
                proc_vals['purchase_auto_merge'] = context.get(
                    'purchase_auto_merge', True
                )
                proc_id = proc_obj.create(cr, uid, proc_vals, context=context)
                proc_ids.append(proc_id)
                wf_service.trg_validate(
                    uid, 'procurement.order', proc_id, 'button_confirm', cr
                )
                orderpoint_obj.write(
                    cr, uid, [op.id],
                    {'procurement_id': proc_id},
                    context=context
                )
                wf_service.trg_validate(
                    uid, 'procurement.order', proc_id, 'button_check', cr
                )
        return proc_ids

