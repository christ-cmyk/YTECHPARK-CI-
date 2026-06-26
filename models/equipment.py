from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


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
    employee_id = fields.Many2one('hr.employee', string='Employé affecté', tracking=True, domain=[('active', '=', True)])
    licence_ids = fields.One2many('it.licence', 'equipment_id', string='Licences installées')
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
            if rec.purchase_value is not False and rec.purchase_value <= 0:
                raise ValidationError(
                    f"❌ Équipement '{rec.name}' : La valeur d'achat doit être supérieure à 0 FCFA. "
                    f"Un équipement sans valeur ne peut pas être enregistré dans le parc."
                )

    @api.constrains('purchase_date')
    def _check_purchase_date(self):
        for rec in self:
            if rec.purchase_date and rec.purchase_date > fields.Date.today():
                raise ValidationError(
                    f"❌ Équipement '{rec.name}' : La date d'achat ({rec.purchase_date}) "
                    f"ne peut pas être postérieure à la date d'aujourd'hui ({fields.Date.today()}). "
                    f"Vérifiez la date saisie."
                )

    @api.constrains('purchase_date', 'warranty_date')
    def _check_warranty_date(self):
        for rec in self:
            if rec.purchase_date and rec.warranty_date:
                if rec.warranty_date < rec.purchase_date:
                    raise ValidationError(
                        f"❌ Équipement '{rec.name}' : La date de fin de garantie ({rec.warranty_date}) "
                        f"ne peut pas être antérieure à la date d'achat ({rec.purchase_date}). "
                        f"La garantie commence à partir de la date d'achat."
                    )

    @api.constrains('serial_number')
    def _check_serial_number(self):
        for rec in self:
            if rec.serial_number:
                if len(rec.serial_number.strip()) < 3:
                    raise ValidationError(
                        f"❌ Équipement '{rec.name}' : Le numéro de série '{rec.serial_number}' "
                        f"est trop court (minimum 3 caractères). "
                        f"Exemple de format valide : SN-DELL-00412"
                    )
                if ' ' in rec.serial_number:
                    raise ValidationError(
                        f"❌ Équipement '{rec.name}' : Le numéro de série '{rec.serial_number}' "
                        f"ne doit pas contenir d'espaces. "
                        f"Exemple de format valide : SN-DELL-00412"
                    )

    def action_assign(self):
        for rec in self:
            if not rec.employee_id:
                raise UserError(
                    f"❌ Impossible d'affecter '{rec.name}' : Aucun employé sélectionné. "
                    f"Veuillez d'abord renseigner l'employé dans l'onglet 'Informations générales' "
                    f"avant de procéder à l'affectation."
                )
            if not rec.employee_id.active:
                raise UserError(
                    f"❌ Impossible d'affecter '{rec.name}' à {rec.employee_id.name} : "
                    f"Cet employé est archivé dans le système. "
                    f"Veuillez sélectionner un employé actif."
                )
        return self.write({'state': 'assigned'})

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
            planned_interventions = self.env['it.intervention'].search([
                ('equipment_id', '=', rec.id),
                ('state', '=', 'planned'),
            ])
            if planned_interventions:
                raise UserError(
                    f"❌ Impossible de retirer '{rec.name}' : "
                    f"Cet équipement a {len(planned_interventions)} intervention(s) planifiée(s) en attente. "
                    f"Veuillez d'abord terminer ou annuler ces interventions avant de retirer l'équipement."
                )
        return self.write({'state': 'retired'})

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
