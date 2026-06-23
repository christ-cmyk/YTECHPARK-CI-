from odoo import models, fields, api
from odoo.exceptions import UserError


class Affectation(models.Model):
    _name = 'it.affectation'
    _description = 'Affectation d\'équipement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'equipment_id'
    _order = 'date_start desc'

    equipment_id = fields.Many2one('it.equipment', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employé')
    department_id = fields.Many2one('hr.department', string='Département')
    date_start = fields.Date(required=True, default=fields.Date.today)
    date_end = fields.Date(string='Date de fin')
    reason = fields.Text(string='Motif', required=True)
    active = fields.Boolean(default=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_end < rec.date_start:
                    raise UserError(
                        "La date de fin d'affectation ne peut pas être antérieure à la date de début. "
                        "Veuillez vérifier les dates."
                    )
            if rec.date_start and rec.date_start > fields.Date.today():
                raise UserError(
                    f"La date de début d'affectation ({rec.date_start}) ne peut pas être dans le futur. "
                    "Veuillez saisir une date valide."
                )

    @api.constrains('equipment_id', 'date_start', 'date_end')
    def _check_overlap(self):
        for rec in self:
            if rec.date_end:
                continue
            overlapping = self.env['it.affectation'].search([
                ('equipment_id', '=', rec.equipment_id.id),
                ('id', '!=', rec.id),
                ('active', '=', True),
                ('date_end', '=', False),
            ], limit=1)
            if overlapping:
                raise UserError(
                    f"L'équipement \"{rec.equipment_id.name}\" est déjà affecté à un employé. "
                    "Veuillez clore l'affectation en cours avant d'en créer une nouvelle."
                )
