from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class WizardRapportMaintenances(models.TransientModel):
    _name = 'it.wizard.rapport.maintenances'
    _description = 'Filtre rapport maintenances par période'

    date_start = fields.Date(string='Date début', required=True,
        default=lambda self: fields.Date.today().replace(day=1))
    date_end = fields.Date(string='Date fin', required=True,
        default=fields.Date.today)
    type_filter = fields.Selection([
        ('all', 'Correctives + Préventives'),
        ('corrective', 'Correctives uniquement'),
        ('preventive', 'Préventives uniquement'),
    ], string="Type d'intervention", default='all', required=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_end < rec.date_start:
                    raise ValidationError(
                        "❌ La date de fin doit être postérieure à la date de début."
                    )

    def action_print(self):
        self.ensure_one()
        domain = [
            ('date_start', '>=', fields.Datetime.from_string(str(self.date_start) + ' 00:00:00')),
            ('date_start', '<=', fields.Datetime.from_string(str(self.date_end) + ' 23:59:59')),
        ]
        if self.type_filter != 'all':
            domain.append(('type', '=', self.type_filter))
        interventions = self.env['it.intervention'].search(domain, order='date_start asc')
        if not interventions:
            raise UserError(
                f"❌ Aucune intervention trouvée entre le {self.date_start} et le {self.date_end}. "
                f"Modifiez la période ou le type de filtre."
            )
        return self.env.ref('it_parc.action_report_maintenances').report_action(interventions)
