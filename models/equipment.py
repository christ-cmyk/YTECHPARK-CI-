from odoo import models, fields, api
from odoo.exceptions import UserError


class EquipmentCategory(models.Model):
    _name = 'it.equipment.category'
    _description = 'Catégorie d\'équipement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    description = fields.Text(string='Description')


class Equipment(models.Model):
    _name = 'it.equipment'
    _description = 'Équipement informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    _sql_constraints = [
        ('serial_number_uniq', 'unique(serial_number)', 'Le numéro de série doit être unique !')
    ]

    name = fields.Char(required=True, tracking=True)
    category_id = fields.Many2one('it.equipment.category', string='Catégorie', required=True)
    serial_number = fields.Char(string='Numéro de série', required=True, copy=False)
    purchase_date = fields.Date(string="Date d'achat")
    warranty_date = fields.Date(string='Fin de garantie', tracking=True)
    purchase_value = fields.Float(string="Valeur d'achat (FCFA)", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employé affecté', tracking=True)
    department_id = fields.Many2one('hr.department', string='Département', tracking=True)
    location = fields.Char(string='Localisation (site)')
    notes = fields.Text(string='Notes techniques')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('assigned', 'Affecté'),
        ('maintenance', 'En maintenance'),
        ('retired', 'Retiré'),
    ], default='draft', tracking=True, string='État')
    affectation_ids = fields.One2many('it.affectation', 'equipment_id', string='Historique affectations')
    intervention_ids = fields.One2many('it.intervention', 'equipment_id', string='Interventions')

    @api.constrains('purchase_value')
    def _check_purchase_value(self):
        for rec in self:
            if not rec.purchase_value or rec.purchase_value <= 0:
                raise UserError(
                    "La valeur d'achat de l'équipement doit être supérieure à zéro. "
                    "Veuillez renseigner le prix d'acquisition réel."
                )

    @api.constrains('purchase_date')
    def _check_purchase_date(self):
        for rec in self:
            if rec.purchase_date and rec.purchase_date > fields.Date.today():
                raise UserError(
                    f"La date d'achat ({rec.purchase_date}) ne peut pas être dans le futur. "
                    "Veuillez saisir une date d'achat valide (passée ou aujourd'hui)."
                )

    @api.constrains('warranty_date', 'purchase_date')
    def _check_warranty_date(self):
        for rec in self:
            if rec.warranty_date and rec.purchase_date and rec.warranty_date < rec.purchase_date:
                raise UserError(
                    "La date de fin de garantie ne peut pas être antérieure à la date d'achat. "
                    "Veuillez vérifier les dates saisies."
                )

    def action_assign(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Seuls les équipements en brouillon peuvent être affectés.")
            rec.state = 'assigned'

    def action_maintenance(self):
        for rec in self:
            if rec.state != 'assigned':
                raise UserError("Seuls les équipements affectés peuvent passer en maintenance.")
            rec.state = 'maintenance'

    def action_return_assigned(self):
        for rec in self:
            if rec.state != 'maintenance':
                raise UserError("Seuls les équipements en maintenance peuvent revenir en affectation.")
            rec.state = 'assigned'

    def action_retire(self):
        for rec in self:
            if rec.state not in ('draft', 'assigned', 'maintenance'):
                raise UserError("Cet équipement ne peut pas être retiré.")
            rec.state = 'retired'

    def action_open_reaffectation_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Réaffecter l'équipement",
            'res_model': 'it.wizard.reaffectation',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_equipment_id': self.id},
        }
