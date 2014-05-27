from openerp.osv import fields
from openerp.osv.orm import Model


class ConnectorCheckpoint(Model):
    _inherit = 'connector.checkpoint'

    def _get_company_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for checkpoint in self.browse(cr, uid, ids, context=context):
            if checkpoint.backend_id:
                backend = checkpoint.backend_id
                if backend.company_id:
                    result[checkpoint.id] = backend.company_id.id
                    continue
            if checkpoint.record:
                record = checkpoint.record
                if record.company_id:
                    result[checkpoint.id] = record.company_id.id
        return result            

    _columns = {
        'company_id': fields.function(
            _get_company_id, type='many2one', obj='res.company', store=True,
            string="Company"
        ),
    }
