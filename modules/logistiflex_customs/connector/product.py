from openerp import SUPERUSER_ID
from openerp.addons.connector.unit.mapper import mapping, only_create
from openerp.addons.prestashoperpconnect_export_price.product import ProductMapper
from openerp.addons.prestashoperpconnect_export_price.product_combination import (
    ProductCombinationMapper,
)
from openerp.addons.prestashoperpconnect.unit.mapper import SupplierInfoMapper
from openerp.addons.prestashoperpconnect.unit.import_synchronizer import (
    ProductRecordImport)
from openerp.addons.prestashoperpconnect_export_price.product import ProductPriceExporter
from openerp.addons.prestashoperpconnect_export_price.product_combination import CombinationPriceExporter
from .backend import prestashop_logistiflex
from openerp.osv import orm
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector_ecommerce.event import on_product_price_changed


@prestashop_logistiflex
class LogistiflexProductMapper(ProductMapper):

    @mapping
    @only_create
    def manual_cost_price(self, record):
        return {'manual_cost_price': record['wholesale_price']}

    def _product_code_exists(self, code):
        company_obj = self.session.pool.get('res.company')
        company_ids = company_obj.search(self.session.cr, SUPERUSER_ID, [])
        ctx = self.session.context.copy()
        ctx['active_test'] = False

        model = self.session.pool.get('product.product')
        product_ids = model.search(self.session.cr, SUPERUSER_ID, [
            ('default_code', '=', code),
            ('company_id', 'in', company_ids),
        ], context=ctx)
        return len(product_ids) > 0


@prestashop_logistiflex
class LogistiflexProductCombinationMapper(ProductCombinationMapper):

    @mapping
    @only_create
    def manual_cost_price(self, record):
        price = float(record['wholesale_price'])
        main_product = self.main_product(record)
        price = main_product.manual_cost_price + price
        return {'manual_cost_price': price}

    def _product_code_exists(self, code):
        company_obj = self.session.pool.get('res.company')
        company_ids = company_obj.search(self.session.cr, SUPERUSER_ID, [])
        ctx = self.session.context.copy()
        ctx['active_test'] = False

        model = self.session.pool.get('product.product')
        product_ids = model.search(self.session.cr, SUPERUSER_ID, [
            ('default_code', '=', code),
            ('company_id', 'in', company_ids),
        ], context=ctx)
        return len(product_ids) > 0

#@prestashop_logistiflex
#class LogistiflexProductRecordImport(ProductRecordImport):
#
#    def _after_import(self, erp_id):
#        self.session._context.update({'update_price': True})
#        return super(LogistiflexProductRecordImport, self)._after_import(erp_id)
#
#    def run(self, prestashop_id):
#        self.session._context.update({'update_price': True})
#        return super(LogistiflexProductRecordImport, self).run(prestashop_id)


@prestashop_logistiflex
class LogistiflexSupplierInfoMapper(SupplierInfoMapper):
    @mapping
    def supplier_product_id(self, record):
        partner_id = self.name(record)['name']
        partner = self.session.browse('res.partner', partner_id)
        if (not partner.partner_company_id or
                not record['product_supplier_reference']):
            return {}
        combination_obj = self.session.pool['prestashop.product.combination']
        combination_ids = combination_obj.search(
            self.session.cr,
            SUPERUSER_ID,
            [
                ('company_id', '=', partner.partner_company_id.id),
                ('reference', '=', record['product_supplier_reference']),
                ('purchase_ok', '=', True),
                ('type', '!=', 'service'),
            ],
        )
        if len(combination_ids) == 1:
            combination = combination_obj.browse(self.session.cr, SUPERUSER_ID, combination_ids[0])
            return {'supplier_product_id': combination.openerp_id.id}

        product_obj = self.session.pool['prestashop.product.product']
        product_ids = product_obj.search(
            self.session.cr,
            SUPERUSER_ID,
            [
                ('company_id', '=', partner.partner_company_id.id),
                ('reference', '=', record['product_supplier_reference']),
                ('purchase_ok', '=', True),
                ('type', '!=', 'service'),
            ]
        )
        if len(product_ids) != 1:
            return {}
        product = product_obj.read(self.session.cr, SUPERUSER_ID, product_ids[0], ['openerp_id'])

        return {'supplier_product_id': product['openerp_id'][0]}

class product_template(orm.Model):
    _inherit = 'product.template'

    def _price_changed(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if vals.get('manual_cost_price', False):
            session = ConnectorSession(cr, uid, context=context)
            product_obj = self.pool['product.product']
            product_ids = product_obj.search(cr, uid,
                                             [('product_tmpl_id', 'in', ids)],
                                             context=context)
            if context.get('from_product_ids'):
                product_ids = list(set(product_ids) -
                                   set(context['from_product_ids']))
            for prod_id in product_ids:
                on_product_price_changed.fire(session,
                                              product_obj._name,
                                              prod_id)
            return
        else:
            super(product_template, self)._price_changed(cr, uid, ids, vals,
                                                         context=context)

class product_product(orm.Model):
    _inherit = 'product.product'

    def _price_changed(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if vals.get('manual_cost_price', False):
            session = ConnectorSession(cr, uid, context=context)
            for prod_id in ids:
                on_product_price_changed.fire(session, self._name, prod_id)
        else:
            super(product_product, self)._price_changed(cr, uid, ids, vals,
                                                         context=context)

@prestashop(replacing=ProductPriceExporter)
class PurchaseProductPriceExporter(ProductPriceExporter):
    _model_name = ['prestashop.product.product']

    def get_datas(self, binding):
        res = super(PurchaseProductPriceExporter, self).get_datas(binding)
        res['wholesale_price'] = binding.manual_cost_price or binding.standard_price
        return res

@prestashop(replacing=CombinationPriceExporter)
class PurchasecombinationPriceExporter(CombinationPriceExporter):
    _model_name = ['prestashop.product.combination']

    def get_datas(self, binding):
        res = super(PurchasecombinationPriceExporter, self).get_datas(binding)
        res['wholesale_price'] = binding.manual_cost_price or binding.standard_price
        return res

