from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardRenouvellement(models.TransientModel):
    _name = 'it.wizard.renouvellement'
    _description = 'Wizard de renouvellement de contrat'

    contrat_id = fields.Many2one('it.contrat', string='Contrat', required=True)
    new_date_start = fields.Date(string='Nouvelle date de début', required=True, default=fields.Date.today)
    new_date_end = fields.Date(string='Nouvelle date de fin', required=True)
    new_amount = fields.Float(string='Nouveau montant (FCFA)')
    notes = fields.Text(string='Notes de renouvellement')

    def action_confirm(self):
        self.ensure_one()
        if self.new_date_end <= self.new_date_start:
            raise UserError("La nouvelle date de fin doit être postérieure à la nouvelle date de début.")
        old = self.contrat_id
        old.write({'state': 'renewed'})
        new_contrat = old.copy(default={
            'name': f"{old.name} (Renouvelé le {fields.Date.today().strftime('%d/%m/%Y')})",
            'date_start': self.new_date_start,
            'date_end': self.new_date_end,
            'amount': self.new_amount if self.new_amount else old.amount,
            'notes': self.notes,
            'state': 'active',
        })
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Contrats fournisseurs',
            'res_model': 'it.contrat',
            'view_mode': 'form',
            'res_id': new_contrat.id,
            'target': 'current',
        }
        return action
