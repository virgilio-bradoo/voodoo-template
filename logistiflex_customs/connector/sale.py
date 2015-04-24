from .backend import prestashop_logistiflex
from openerp.addons.prestashoperpconnect.unit.mapper import SaleOrderMapper
from openerp.addons.prestashoperpconnect_transaction_id.sale import SaleOrderImportTransaction
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter


@prestashop_logistiflex
class LogistiflexSaleOrderMapper(SaleOrderMapper):

    def _get_discounts_lines(self, record):
        res = super(LogistiflexSaleOrderMapper, self)._get_discounts_lines(
            record)
        index_to_remove = []
        for index, discount_mapper in enumerate(res):
            vals = discount_mapper._data or {}
            if vals.get('name', False):
                if vals['name'].startswith('Discount V'):
                    index_to_remove.append(index)
        res = [j for i, j in enumerate(res) if i not in index_to_remove]
        return res


@prestashop_logistiflex
class LogistiflexSaleOrderImport(SaleOrderImportTransaction):

    def change_prestashop_total(self, erp_id):
        sess = self.session
        presta_sale = sess.browse(self.model._name, erp_id)
        discount_adapter = self.get_connector_unit_for_model(
            GenericAdapter,
            'prestashop.sale.order.line.discount'
        )
        discount_ids = discount_adapter.search({
            'filter[id_order]': self.prestashop_id
        })
        tot_refund = 0.0
        tot_tax_refund = 0.0
        for discount_id in discount_ids:
            discount = discount_adapter.read(discount_id)
            if discount.get('name', {}).startswith('V'):
                tot_refund += float(discount.get('value', '0.0'))
                tot_tax_refund += float(discount.get('value', '0.0')) - float(discount.get('value_tax_excl', '0.0'))
            else:
                continue
        rec = self.prestashop_record
        new_total_paid = float(rec['total_paid']) + tot_refund
        old_total_amount_tax = float(rec['total_paid_tax_incl'])\
                - float(rec['total_paid_tax_excl'])
        new_total_amount_tax = old_total_amount_tax + tot_tax_refund
        sess.write(self.model._name, erp_id, {'total_amount':new_total_paid, 'total_amount_tax': new_total_amount_tax})

    def _after_import(self, erp_id):
        super(LogistiflexSaleOrderImport, self)._after_import(
            erp_id)
        self.change_prestashop_total(erp_id)

