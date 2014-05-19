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

        model = self.session.pool.get('product.product')
        product_ids = model.search(self.session.cr, SUPERUSER_ID, [
            ('default_code', '=', code),
            ('company_id', 'in', company_ids),
        ])
        return len(product_ids) > 0


@prestashop_logistiflex
class LogistiflexProductCombinationMapper(ProductCombinationMapper):
    direct = ProductCombinationMapper.direct + [
        ('wholesale_price', 'manual_cost_price'),
    ]

    def _product_code_exists(self, code):
        company_obj = self.session.pool.get('res.company')
        company_ids = company_obj.search(self.session.cr, SUPERUSER_ID, [])

        model = self.session.pool.get('product.product')
        product_ids = model.search(self.session.cr, SUPERUSER_ID, [
            ('default_code', '=', code),
            ('company_id', 'in', company_ids),
        ])
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
        product_obj = self.session.pool['product.product']
        product_ids = product_obj.search(
            self.session.cr,
            SUPERUSER_ID,
            [
                ('company_id', '=', partner.partner_company_id.id),
                ('default_code', 'like',
                 '%s%%' % record['product_supplier_reference']),
                ('purchase_ok', '=', True),
                ('type', '!=', 'service'),
            ]
        )
        if len(product_ids) != 1:
            return {}
        return {'supplier_product_id': product_ids[0]}
