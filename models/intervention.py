from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Intervention(models.Model):
    _name = 'it.intervention'
    _description = 'Intervention de maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(required=True, default='Nouvelle intervention')
    equipment_id = fields.Many2one('it.equipment', required=True, ondelete='cascade')
    type = fields.Selection([
        ('corrective', 'Corrective'),
        ('preventive', 'Préventive'),
    ], required=True)
    technician_id = fields.Many2one('hr.employee', string='Technicien', required=True)
    date_start = fields.Datetime(string='Début')
    date_end = fields.Datetime(string='Fin')
    duration_hours = fields.Float(string='Durée (heures)', compute='_compute_duration', store=False)
    cost = fields.Float(string='Coût (FCFA)')
    report = fields.Text(string="Rapport d'intervention")
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('done', 'Terminée'),
    ], default='planned', tracking=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_end <= rec.date_start:
                    raise ValidationError(
                        f"❌ Intervention '{rec.name}' : La date de fin ({rec.date_end}) "
                        f"doit être postérieure à la date de début ({rec.date_start}). "
                        f"Vérifiez les horaires saisis."
                    )

    @api.constrains('cost')
    def _check_cost(self):
        for rec in self:
            if rec.cost is not False and rec.cost == 0:
                raise ValidationError(
                    f"❌ Intervention '{rec.name}' : Le coût ne peut pas être 0 FCFA. "
                    f"Si l'intervention est sous garantie, saisissez 1 FCFA symbolique "
                    f"et précisez 'Sous garantie' dans le rapport."
                )
            if rec.cost < 0:
                raise ValidationError(
                    f"❌ Intervention '{rec.name}' : Le coût ({rec.cost} FCFA) "
                    f"ne peut pas être négatif."
                )

    @api.constrains('date_start')
    def _check_date_start_required(self):
        for rec in self:
            if not rec.date_start:
                raise ValidationError(
                    f"❌ Intervention '{rec.name}' : La date de début est obligatoire."
                )

    @api.constrains('state', 'report')
    def _check_report_required(self):
        for rec in self:
            if rec.state == 'done' and not rec.report:
                raise ValidationError(
                    f"❌ Intervention '{rec.name}' : Un rapport d'intervention est obligatoire "
                    f"pour marquer une intervention comme terminée. "
                    f"Renseignez le champ 'Rapport d'intervention' avant de valider."
                )

    @api.constrains('state', 'date_end')
    def _check_date_end_required(self):
        for rec in self:
            if rec.state == 'done' and not rec.date_end:
                raise ValidationError(
                    f"❌ Intervention '{rec.name}' : La date de fin est obligatoire "
                    f"pour marquer une intervention comme terminée. "
                    f"Renseignez la date et l'heure de fin avant de valider."
                )

    def write(self, vals):
        for rec in self:
            if 'state' in vals and vals['state'] != rec.state:
                if vals['state'] == 'done' and rec.state != 'planned':
                    raise UserError("Seules les interventions planifiées peuvent être terminées.")
                if vals['state'] == 'planned' and rec.state != 'done':
                    raise UserError("Seules les interventions terminées peuvent être rouvertes.")
        return super().write(vals)

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                delta = rec.date_end - rec.date_start
                rec.duration_hours = max(delta.total_seconds() / 3600, 0.0)
            else:
                rec.duration_hours = 0.0
