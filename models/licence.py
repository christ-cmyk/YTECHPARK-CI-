from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ItLicence(models.Model):
    _name = 'it.licence'
    _description = 'Licence logicielle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom du logiciel', required=True, tracking=True)
    version = fields.Char(string='Version')
    licence_key = fields.Char(string='Clé de licence', copy=False)
    equipment_id = fields.Many2one(
        'it.equipment',
        string='Équipement hôte',
        help="PC ou serveur sur lequel cette licence est installée",
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Utilisateur assigné',
        domain=[('active', '=', True)],
        tracking=True
    )
    contrat_id = fields.Many2one(
        'it.contrat',
        string='Contrat associé',
        help="Contrat fournisseur couvrant cette licence"
    )
    date_expiry = fields.Date(string="Date d'expiration", tracking=True)
    days_remaining = fields.Integer(
        string='Jours restants',
        compute='_compute_days_remaining',
        store=True
    )
    licence_type = fields.Selection([
        ('perpetual', 'Perpétuelle'),
        ('subscription', 'Abonnement annuel'),
        ('trial', 'Essai'),
    ], string='Type de licence', default='subscription', required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expirée'),
        ('revoked', 'Révoquée'),
    ], default='active', tracking=True, string='État')
    notes = fields.Text()

    @api.depends('date_expiry')
    def _compute_days_remaining(self):
        for rec in self:
            if rec.date_expiry:
                rec.days_remaining = (rec.date_expiry - fields.Date.today()).days
            else:
                rec.days_remaining = 0

    @api.constrains('date_expiry', 'licence_type')
    def _check_expiry(self):
        for rec in self:
            if rec.licence_type == 'subscription' and not rec.date_expiry:
                raise ValidationError(
                    f"❌ Licence '{rec.name}' : Une licence en abonnement "
                    f"doit avoir une date d'expiration."
                )
