from openerp import SUPERUSER_ID
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.prestashoperpconnect.product import ProductMapper
from openerp.addons.prestashoperpconnect.product_combination import (
    ProductCombinationMapper,
)
from openerp.addons.prestashoperpconnect.unit.mapper import SupplierInfoMapper

from .backend import prestashop_logistiflex


@prestashop_logistiflex
class LogistiflexProductMapper(ProductMapper):
    direct = ProductMapper.direct + [
        ('wholesale_price', 'manual_cost_price'),
    ]

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
    def manual_cost_price(self, record):
        print "kkkkk"
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
