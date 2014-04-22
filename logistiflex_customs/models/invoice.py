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
