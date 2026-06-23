from odoo import models, fields, api
from odoo.exceptions import UserError


class Alerte(models.Model):
    _name = 'it.alerte'
    _description = 'Alerte'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(required=True, string="Intitulé de l'alerte")
    type = fields.Selection([
        ('warranty', 'Garantie équipement'),
        ('contract', 'Contrat fournisseur'),
    ], required=True, string="Type d'alerte")
    equipment_id = fields.Many2one('it.equipment', string='Équipement concerné')
    contrat_id = fields.Many2one('it.contrat', string='Contrat concerné')
    date_expiry = fields.Date(string="Date d'expiration", required=True)
    days_before = fields.Integer(string='Jours avant expiration', compute='_compute_days_before', store=False)
    user_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    state = fields.Selection([
        ('open', 'Ouverte'),
        ('done', 'Traitée'),
        ('ignored', 'Ignorée'),
    ], default='open', tracking=True)
    message = fields.Text(string='Message')

    @api.constrains('type', 'equipment_id', 'contrat_id')
    def _check_references(self):
        for rec in self:
            if rec.type == 'warranty' and not rec.equipment_id:
                raise UserError(
                    "Une alerte de type 'Garantie équipement' doit être associée à un équipement. "
                    "Veuillez renseigner l'équipement concerné."
                )
            if rec.type == 'contract' and not rec.contrat_id:
                raise UserError(
                    "Une alerte de type 'Contrat fournisseur' doit être associée à un contrat. "
                    "Veuillez renseigner le contrat concerné."
                )

    @api.constrains('date_expiry')
    def _check_date_expiry(self):
        for rec in self:
            if rec.date_expiry and rec.date_expiry < fields.Date.today() and rec.state == 'open':
                raise UserError(
                    f"La date d'expiration de l'alerte ({rec.date_expiry.strftime('%d/%m/%Y')}) "
                    "est déjà dépassée. Veuillez mettre à jour l'état de l'alerte "
                    "(Traiter ou Ignorer) ou corriger la date."
                )

    @api.depends('date_expiry')
    def _compute_days_before(self):
        for rec in self:
            if rec.date_expiry:
                rec.days_before = (rec.date_expiry - fields.Date.today()).days
            else:
                rec.days_before = 0

    def action_mark_done(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError("Seules les alertes ouvertes peuvent être traitées.")
            rec.state = 'done'

    def action_ignore(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError("Seules les alertes ouvertes peuvent être ignorées.")
            rec.state = 'ignored'

    @api.model
    def _cron_check_alerts(self):
        today = fields.Date.today()
        DELAY_WARRANTY = 30
        DELAY_CONTRACT = 60

        equipments = self.env['it.equipment'].search([
            ('warranty_date', '!=', False),
            ('state', 'not in', ['retired']),
        ])
        for eq in equipments:
            try:
                days_left = (eq.warranty_date - today).days
                if 0 <= days_left <= DELAY_WARRANTY:
                    existing = self.env['it.alerte'].search([
                        ('equipment_id', '=', eq.id),
                        ('type', '=', 'warranty'),
                        ('state', '=', 'open'),
                    ], limit=1)
                    if not existing:
                        self.env['it.alerte'].create({
                            'name': f'[AUTO] Garantie expirante — {eq.name}',
                            'type': 'warranty',
                            'equipment_id': eq.id,
                            'date_expiry': eq.warranty_date,
                            'message': (
                                f'La garantie de l\'équipement "{eq.name}" '
                                f'(S/N : {eq.serial_number}) expire dans '
                                f'{days_left} jour(s). Veuillez contacter le '
                                f'fournisseur pour un renouvellement.'
                            ),
                        })
            except Exception:
                continue

        contrats = self.env['it.contrat'].search([
            ('date_end', '!=', False),
            ('state', '!=', 'renewed'),
        ])
        for ct in contrats:
            try:
                days_left = (ct.date_end - today).days
                if 0 <= days_left <= DELAY_CONTRACT:
                    existing = self.env['it.alerte'].search([
                        ('contrat_id', '=', ct.id),
                        ('type', '=', 'contract'),
                        ('state', '=', 'open'),
                    ], limit=1)
                    if not existing:
                        self.env['it.alerte'].create({
                            'name': f'[AUTO] Contrat expirant — {ct.name}',
                            'type': 'contract',
                            'contrat_id': ct.id,
                            'date_expiry': ct.date_end,
                            'message': (
                                f'Le contrat "{ct.name}" avec le fournisseur '
                                f'{ct.partner_id.name} expire dans {days_left} '
                                f'jour(s) (montant : {ct.amount:,.0f} FCFA). '
                                f'Veuillez lancer un renouvellement.'
                            ),
                        })
            except Exception:
                continue
