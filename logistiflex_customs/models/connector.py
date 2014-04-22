from openerp.osv import fields
from openerp.osv.orm import Model


class ConnectorCheckpoint(Model):
    _inherit = 'connector.checkpoint'

    def _get_company_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for checkpoint in self.browse(cr, uid, fields, context=context):
            if checkpoint.backend_id.company_id:
                result[checkpoint.id] = checkpoint.backend_id.company_id
                continue
            if checkpoint.record.company_id:
                result[checkpoint.id] = checkpoint.record.company_id
        return result            

    _columns = {
        'company_id': fields.function(
            _get_company_id, type='many2one', obj='res.company',
            string="Company"
        ),
    }
