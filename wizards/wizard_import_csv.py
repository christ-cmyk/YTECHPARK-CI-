from odoo import models, fields, api
import base64
import csv
import io


class WizardImportCsv(models.TransientModel):
    _name = 'it.wizard.import.csv'
    _description = 'Import en masse d\'équipements via CSV'

    csv_file = fields.Binary(string='Fichier CSV', required=True, attachment=False)
    csv_filename = fields.Char(string='Nom du fichier')
    result_message = fields.Text(string='Rapport d\'import', readonly=True)

    def action_import(self):
        self.ensure_one()

        created_count = 0
        skipped_count = 0
        error_lines = []

        csv_data = base64.b64decode(self.csv_file)
        reader = csv.DictReader(io.StringIO(csv_data.decode('utf-8-sig')))

        for i, row in enumerate(reader, start=2):
            try:
                serial = row.get('serial_number', '').strip()
                if not serial:
                    error_lines.append(f'Ligne {i} : numéro de série manquant')
                    continue

                existing = self.env['it.equipment'].search([('serial_number', '=', serial)], limit=1)
                if existing:
                    skipped_count += 1
                    continue

                name = row.get('name', '').strip()
                if not name:
                    name = f"Équipement ({serial})"
                    error_lines.append(f'Ligne {i} : nom manquant, généré automatiquement')

                cat_name = row.get('category', '').strip()
                category = self.env['it.equipment.category'].search(
                    [('name', '=like', cat_name)], limit=1
                ) if cat_name else False
                if not category and cat_name:
                    category = self.env['it.equipment.category'].search(
                        [('name', 'ilike', cat_name)], limit=1
                    )
                    if not category:
                        error_lines.append(f'Ligne {i} : catégorie "{cat_name}" introuvable')

                purchase_value = 0
                pv = row.get('purchase_value', '').strip()
                if pv:
                    purchase_value = float(pv)
                if purchase_value <= 0:
                    error_lines.append(f'Ligne {i} : valeur d\'achat manquante ou nulle')

                purchase_date = row.get('purchase_date', '').strip() or False
                warranty_date = row.get('warranty_date', '').strip() or False

                vals = {
                    'name': name,
                    'serial_number': serial,
                    'location': row.get('location', '').strip(),
                    'purchase_value': purchase_value or 1,
                }
                if category:
                    vals['category_id'] = category.id
                if purchase_date:
                    vals['purchase_date'] = purchase_date
                if warranty_date:
                    vals['warranty_date'] = warranty_date

                self.env['it.equipment'].create(vals)
                created_count += 1

            except Exception as e:
                error_lines.append(f'Ligne {i} : {str(e)}')

        report = f'Créés : {created_count}\nIgnorés (doublons) : {skipped_count}\n'
        if error_lines:
            report += f'Erreurs : {len(error_lines)}\n' + '\n'.join(error_lines)
        else:
            report += 'Erreurs : 0'

        self.result_message = report
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.wizard.import.csv',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
