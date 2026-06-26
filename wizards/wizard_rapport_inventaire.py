from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardRapportInventaire(models.TransientModel):
    _name = 'it.wizard.rapport.inventaire'
    _description = 'Filtre rapport inventaire'

    filter_type = fields.Selection([
        ('all', 'Tous les équipements'),
        ('department', 'Par département'),
        ('category', 'Par catégorie'),
        ('state', 'Par état'),
    ], string='Filtrer par', default='all', required=True)

    department_id = fields.Many2one('hr.department', string='Département')
    category_id = fields.Many2one('it.equipment.category', string='Catégorie')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('assigned', 'Affecté'),
        ('maintenance', 'En maintenance'),
        ('retired', 'Retiré'),
    ], string='État')

    def action_print(self):
        self.ensure_one()
        domain = []
        if self.filter_type == 'department' and self.department_id:
            domain = [('department_id', '=', self.department_id.id)]
        elif self.filter_type == 'category' and self.category_id:
            domain = [('category_id', '=', self.category_id.id)]
        elif self.filter_type == 'state' and self.state:
            domain = [('state', '=', self.state)]
        equipments = self.env['it.equipment'].search(domain)
        if not equipments:
            raise UserError(
                f"❌ Aucun équipement trouvé avec ce filtre. "
                f"Modifiez les critères de recherche."
            )
        return self.env.ref('it_parc.action_report_inventaire').report_action(equipments)
