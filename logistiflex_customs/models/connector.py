from openerp.osv import fields
from openerp.osv.orm import Model


class ConnectorCheckpoint(Model):
    _inherit = 'connector.checkpoint'

    def get_object(self, cr, uid, reference, context=None):
        model, id = reference.split(',', 2)
        return self.pool.get(model).browse(cr, uid, id, context=context)

    def _get_company_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for checkpoint in self.browse(cr, uid, fields, context=context):
            if checkpoint.backend_id:
                backend = self.get_object(cr, uid, checkpoint.backend_id, context=context)
                if backend.company_id:
                    result[checkpoint.id] = backend.company_id
            if checkpoint.record:
                record = self.get_object(cr, uid, checkpoint.record, context=context)
                if record.company_id:
                    result[checkpoint.id] = backend.company_id
        return result            

    _columns = {
        'company_id': fields.function(
            _get_company_id, type='many2one', obj='res.company', store=True,
            string="Company"
        ),
    }
