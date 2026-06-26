from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Contrat(models.Model):
    _name = 'it.contrat'
    _description = 'Contrat fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(required=True, string='Intitulé du contrat')
    partner_id = fields.Many2one('res.partner', string='Fournisseur', required=True)
    date_start = fields.Date(required=True, string='Date de début')
    date_end = fields.Date(required=True, string='Date de fin', tracking=True)
    amount = fields.Float(string='Montant (FCFA)')
    equipment_ids = fields.Many2many('it.equipment', string='Équipements couverts')
    days_remaining = fields.Integer(string='Jours restants', compute='_compute_days_remaining', store=False)
    state = fields.Selection([
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('renewed', 'Renouvelé'),
    ], default='active', tracking=True)
    renewal_blocked = fields.Boolean(
        string='Renouvellement bloqué',
        compute='_compute_renewal_blocked',
        store=False
    )
    notes = fields.Text()

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_end <= rec.date_start:
                    raise ValidationError(
                        f"❌ Contrat '{rec.name}' : La date de fin ({rec.date_end}) "
                        f"doit être postérieure à la date de début ({rec.date_start}). "
                        f"Un contrat ne peut pas se terminer avant de commencer."
                    )

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(
                    f"❌ Contrat '{rec.name}' : Le montant ({rec.amount} FCFA) "
                    f"doit être supérieur à 0 FCFA. "
                    f"Renseignez le montant réel du contrat fournisseur."
                )

    @api.constrains('state', 'date_end')
    def _check_state_active(self):
        for rec in self:
            if rec.state == 'active' and rec.date_end and rec.date_end < fields.Date.today():
                raise UserError(
                    f"Le contrat \"{rec.name}\" est marqué comme actif mais sa date de fin "
                    f"({rec.date_end.strftime('%d/%m/%Y')}) est déjà dépassée. "
                    "Veuillez mettre à jour l'état du contrat (Expiré ou Renouvelé)."
                )

    @api.depends('state', 'date_start')
    def _compute_renewal_blocked(self):
        for rec in self:
            if rec.state == 'renewed' and rec.date_start:
                days_since_renewal = (fields.Date.today() - rec.date_start).days
                rec.renewal_blocked = days_since_renewal < 5
            else:
                rec.renewal_blocked = False

    @api.depends('date_end')
    def _compute_days_remaining(self):
        for rec in self:
            if rec.date_end:
                rec.days_remaining = (rec.date_end - fields.Date.today()).days
            else:
                rec.days_remaining = 0

    def action_open_renouvellement_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Renouveler le contrat",
            'res_model': 'it.wizard.renouvellement',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contrat_id': self.id},
        }
