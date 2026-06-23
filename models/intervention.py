from odoo import models, fields, api
from odoo.exceptions import UserError


class Intervention(models.Model):
    _name = 'it.intervention'
    _description = 'Intervention de maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(required=True, default=lambda self: self._default_name())
    equipment_id = fields.Many2one('it.equipment', required=True, ondelete='cascade')
    type = fields.Selection([
        ('corrective', 'Corrective'),
        ('preventive', 'Préventive'),
    ], required=True)
    technician_id = fields.Many2one('hr.employee', string='Technicien', required=True)
    date_start = fields.Datetime(required=True, string='Début')
    date_end = fields.Datetime(string='Fin')
    duration_hours = fields.Float(string='Durée (heures)', compute='_compute_duration', store=False)
    cost = fields.Float(string='Coût (FCFA)')
    report = fields.Text(string="Rapport d'intervention")
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('done', 'Terminée'),
    ], default='planned', tracking=True)

    def _default_name(self):
        return f"Intervention — {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}"

    @api.constrains('date_start', 'date_end', 'state')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise UserError(
                    "La date de fin de l'intervention ne peut pas être antérieure à la date de début. "
                    "Veuillez vérifier les dates saisies."
                )
            if rec.state == 'done' and rec.date_end and rec.date_end > fields.Datetime.now():
                raise UserError(
                    f"La date de fin d'une intervention terminée ({rec.date_end.strftime('%d/%m/%Y %H:%M')}) "
                    "ne peut pas être dans le futur. Veuillez saisir une date valide."
                )

    @api.constrains('cost')
    def _check_cost(self):
        for rec in self:
            if rec.cost and rec.cost < 0:
                raise UserError(
                    "Le coût de l'intervention ne peut pas être négatif. "
                    "Veuillez saisir un montant valide."
                )

    @api.constrains('state', 'date_end', 'report')
    def _check_done_fields(self):
        for rec in self:
            if rec.state == 'done':
                if not rec.date_end:
                    raise UserError(
                        "Vous devez renseigner la date de fin avant de clôturer l'intervention."
                    )
                if not rec.report:
                    raise UserError(
                        "Vous devez rédiger un rapport d'intervention avant de clôturer."
                    )

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                delta = rec.date_end - rec.date_start
                rec.duration_hours = max(delta.total_seconds() / 3600, 0.0)
            else:
                rec.duration_hours = 0.0

    def action_done(self):
        for rec in self:
            if rec.state != 'planned':
                raise UserError("Seules les interventions planifiées peuvent être terminées.")
            if not rec.date_end:
                raise UserError("Veuillez renseigner la date de fin avant de terminer l'intervention.")
            rec.write({'state': 'done'})

    def action_back_planned(self):
        for rec in self:
            if rec.state != 'done':
                raise UserError("Seules les interventions terminées peuvent être rouvertes.")
            rec.write({'state': 'planned'})
