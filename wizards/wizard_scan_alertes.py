from odoo import models, fields, api


class WizardScanAlertes(models.TransientModel):
    _name = 'it.wizard.scan.alertes'
    _description = 'Scan manuel des alertes'

    delay_warranty = fields.Integer(
        string='Alerter X jours avant fin de garantie',
        default=30, required=True
    )
    delay_contract = fields.Integer(
        string='Alerter X jours avant fin de contrat',
        default=30, required=True
    )
    result_message = fields.Text(string='Résultat du scan', readonly=True)

    def action_scan(self):
        self.ensure_one()
        created = 0
        today = fields.Date.today()

        equipments = self.env['it.equipment'].search([
            ('warranty_date', '!=', False),
            ('state', 'not in', ['retired']),
        ])
        for eq in equipments:
            days_left = (eq.warranty_date - today).days
            if 0 <= days_left <= self.delay_warranty:
                existing = self.env['it.alerte'].search([
                    ('equipment_id', '=', eq.id),
                    ('type', '=', 'warranty'),
                    ('state', '=', 'open'),
                ], limit=1)
                if not existing:
                    self.env['it.alerte'].create({
                        'name': f'Garantie expirante — {eq.name}',
                        'type': 'warranty',
                        'equipment_id': eq.id,
                        'date_expiry': eq.warranty_date,
                        'message': f'La garantie de {eq.name} expire dans {days_left} jour(s).',
                    })
                    created += 1

        contrats = self.env['it.contrat'].search([
            ('date_end', '!=', False),
            ('state', '!=', 'renewed'),
        ])
        for ct in contrats:
            days_left = (ct.date_end - today).days
            if 0 <= days_left <= self.delay_contract:
                existing = self.env['it.alerte'].search([
                    ('contrat_id', '=', ct.id),
                    ('type', '=', 'contract'),
                    ('state', '=', 'open'),
                ], limit=1)
                if not existing:
                    self.env['it.alerte'].create({
                        'name': f'Contrat expirant — {ct.name}',
                        'type': 'contract',
                        'contrat_id': ct.id,
                        'date_expiry': ct.date_end,
                        'message': f'Le contrat {ct.name} expire dans {days_left} jour(s).',
                    })
                    created += 1

        self.result_message = f'Scan terminé. {created} nouvelle(s) alerte(s) créée(s).'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.wizard.scan.alertes',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
