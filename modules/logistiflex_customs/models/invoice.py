from openerp.osv.orm import Model


class AccountInvoice(Model):
    _inherit = 'account.invoice'

    def invoice_validate(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).invoice_validate(
            cr, uid, ids, context=context
        )
        for invoice in self.browse(cr, uid, ids, context=context):
            if not invoice.partner_id.partner_company_id:
                continue
            invoice.create_intercompany_invoice()
        return res

    def _get_refund_vals(self, cr, uid, partner_id, refund_type, company_id,
                         origin, context=None):
        partner_obj = self.pool['res.partner']
        journal_obj = self.pool['account.journal']

        onchange_vals = self.onchange_partner_id(
            cr, uid, False, refund_type, partner_id,
            date_invoice=False,
            payment_term=False,
            partner_bank_id=False,
            company_id=company_id
        )
        invoice_vals = onchange_vals['value']
        if refund_type == 'out_refund':
            journal_type = 'sale_refund'
        elif refund_type == 'in_refund':
            journal_type = 'purchase_refund'
        journal_ids = journal_obj.search(
            cr, uid, [
                ('company_id', '=', company_id),
                ('type', '=', journal_type),
            ],
            context=context
        )
        invoice_vals.update({
            'partner_id': partner_id,
            'type': refund_type,
            'origin': origin,
            'name': 'Intercompany refund from %s' % origin,
            'journal_id': journal_ids and journal_ids[0] or False,
        })
        return invoice_vals

    def get_refund_line_vals(self, cr, uid, partner_id, product_id, qty,
                             price, origin, company_id, context=None):
        invoice_line_obj = self.pool['account.invoice.line']
        onchange_vals = invoice_line_obj.product_id_change(
            cr, uid, False,
            product_id,
            False,
            qty=0,
            name=False,
            type='in_invoice',
            partner_id=partner_id,
            fposition_id=False,
            price_unit=False,
            currency_id=False,
            context=context,
            company_id=company_id
        )
        line_vals = onchange_vals['value']
        line_vals.update({
            'invoice_line_tax_id': [
                (6, 0, onchange_vals['value']['invoice_line_tax_id'])
        ]})
        product = self.pool['product.product'].browse(cr, uid, product_id, context=context)
        line_vals.update({
            'origin': origin,
            'name': origin + '-' + product.name,
            'price_unit': price,
            'quantity': qty,
            'product_id': product_id,
            'company_id': company_id,
        })
        return line_vals

