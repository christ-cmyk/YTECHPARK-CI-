from odoo import models, fields, api


class ItInventaireSnapshot(models.Model):
    _name = 'it.inventaire.snapshot'
    _description = "Snapshot d'inventaire"
    _order = 'date_snapshot desc'

    name = fields.Char(string='Référence', required=True)
    date_snapshot = fields.Datetime(
        string='Date du snapshot',
        default=fields.Datetime.now,
        readonly=True
    )
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        readonly=True
    )
    total_equipment = fields.Integer(string='Total équipements', readonly=True)
    total_assigned = fields.Integer(string='Affectés', readonly=True)
    total_maintenance = fields.Integer(string='En maintenance', readonly=True)
    total_retired = fields.Integer(string='Retirés', readonly=True)
    total_draft = fields.Integer(string='Brouillons', readonly=True)
    total_value = fields.Float(string='Valeur totale (FCFA)', readonly=True)
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many(
        'it.inventaire.snapshot.line',
        'snapshot_id',
        string='Détail équipements',
        readonly=True
    )

    def action_generate_snapshot(self):
        self.ensure_one()
        Equipment = self.env['it.equipment']
        all_eq = Equipment.search([])
        lines = []
        for eq in all_eq:
            lines.append((0, 0, {
                'equipment_id': eq.id,
                'name': eq.name,
                'serial_number': eq.serial_number,
                'category': eq.category_id.name if eq.category_id else '',
                'employee': eq.employee_id.name if eq.employee_id else '',
                'department': eq.department_id.name if eq.department_id else '',
                'location': eq.location or '',
                'state': eq.state,
                'purchase_value': eq.purchase_value,
                'warranty_date': eq.warranty_date,
            }))
        self.write({
            'total_equipment': len(all_eq),
            'total_assigned': len(all_eq.filtered(lambda e: e.state == 'assigned')),
            'total_maintenance': len(all_eq.filtered(lambda e: e.state == 'maintenance')),
            'total_retired': len(all_eq.filtered(lambda e: e.state == 'retired')),
            'total_draft': len(all_eq.filtered(lambda e: e.state == 'draft')),
            'total_value': sum(all_eq.mapped('purchase_value')),
            'line_ids': lines,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Snapshot généré',
                'message': f'Inventaire du {fields.Datetime.now()} : {len(all_eq)} équipements capturés.',
                'type': 'success',
            }
        }


class ItInventaireSnapshotLine(models.Model):
    _name = 'it.inventaire.snapshot.line'
    _description = "Ligne de snapshot d'inventaire"

    snapshot_id = fields.Many2one('it.inventaire.snapshot', ondelete='cascade')
    equipment_id = fields.Many2one('it.equipment', string='Équipement')
    name = fields.Char(string='Nom')
    serial_number = fields.Char(string='N° Série')
    category = fields.Char(string='Catégorie')
    employee = fields.Char(string='Employé')
    department = fields.Char(string='Département')
    location = fields.Char(string='Site')
    state = fields.Char(string='État')
    purchase_value = fields.Float(string='Valeur (FCFA)')
    warranty_date = fields.Date(string='Fin garantie')
