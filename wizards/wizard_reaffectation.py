from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardReaffectation(models.TransientModel):
    _name = 'it.wizard.reaffectation'
    _description = 'Wizard de réaffectation d\'équipement'

    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True)
    employee_id = fields.Many2one('hr.employee', string='Nouvel employé', required=True)
    department_id = fields.Many2one('hr.department', string='Nouveau département', required=True)
    reason = fields.Text(string='Motif de réaffectation', required=True)
    date_start = fields.Date(string='Date effective', required=True, default=fields.Date.today)

    def action_confirm(self):
        self.ensure_one()
        equipment = self.equipment_id
        if self.employee_id == equipment.employee_id and self.department_id == equipment.department_id:
            raise UserError("L'équipement est déjà affecté à cet employé dans ce département.")
        if self.date_start > fields.Date.today():
            raise UserError("La date de réaffectation ne peut pas être dans le futur.")
        active_affectation = self.env['it.affectation'].search([
            ('equipment_id', '=', equipment.id),
            ('active', '=', True),
            ('date_end', '=', False),
        ], limit=1)
        if active_affectation:
            active_affectation.write({'date_end': self.date_start, 'active': False})
        self.env['it.affectation'].create({
            'equipment_id': equipment.id,
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            'reason': self.reason,
            'date_start': self.date_start,
        })
        equipment.write({
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            'state': 'assigned',
        })
        return {'type': 'ir.actions.act_window_close'}
