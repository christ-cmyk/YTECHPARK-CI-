import io
import datetime
import xlsxwriter
from odoo import http
from odoo.http import request, content_disposition


class ItParcExcelExport(http.Controller):

    def _get_workbook_and_formats(self, output):
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        fmt = {}
        fmt['title'] = wb.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#1A3A5C',
            'bottom': 2, 'bottom_color': '#1A3A5C'
        })
        fmt['header'] = wb.add_format({
            'bold': True, 'bg_color': '#1A3A5C', 'font_color': '#FFFFFF',
            'border': 1, 'border_color': '#CCCCCC', 'align': 'center',
            'valign': 'vcenter', 'text_wrap': True
        })
        fmt['cell'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'valign': 'vcenter'
        })
        fmt['cell_alt'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'valign': 'vcenter',
            'bg_color': '#F0F4F8'
        })
        fmt['number'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'num_format': '#,##0',
            'align': 'right'
        })
        fmt['number_alt'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'num_format': '#,##0',
            'align': 'right', 'bg_color': '#F0F4F8'
        })
        fmt['date'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'num_format': 'dd/mm/yyyy'
        })
        fmt['date_alt'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'num_format': 'dd/mm/yyyy',
            'bg_color': '#F0F4F8'
        })
        fmt['total'] = wb.add_format({
            'bold': True, 'bg_color': '#1A3A5C', 'font_color': '#FFFFFF',
            'border': 1, 'num_format': '#,##0', 'align': 'right'
        })
        fmt['total_label'] = wb.add_format({
            'bold': True, 'bg_color': '#1A3A5C', 'font_color': '#FFFFFF',
            'border': 1
        })
        fmt['danger'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'bg_color': '#FCEBEB',
            'font_color': '#A32D2D', 'bold': True, 'align': 'center'
        })
        fmt['warning'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'bg_color': '#FAEEDA',
            'font_color': '#633806', 'bold': True, 'align': 'center'
        })
        fmt['ok'] = wb.add_format({
            'border': 1, 'border_color': '#CCCCCC', 'bg_color': '#EAF3DE',
            'font_color': '#27500A', 'bold': True, 'align': 'center'
        })
        return wb, fmt

    @http.route('/it_parc/export/inventaire', type='http', auth='user')
    def export_inventaire(self, **kwargs):
        output = io.BytesIO()
        wb, fmt = self._get_workbook_and_formats(output)
        ws = wb.add_worksheet('Inventaire')

        equipments = request.env['it.equipment'].search([], order='name asc')

        ws.merge_range('A1:J1',
            f'Inventaire du Parc Informatique — {datetime.date.today().strftime("%d/%m/%Y")}',
            fmt['title'])
        ws.set_row(0, 24)

        headers = ['#', 'Nom', 'Catégorie', 'N° Série', 'Employé',
                   'Département', 'Site', 'Fin garantie', 'Valeur achat (FCFA)', 'État']
        col_widths = [4, 28, 18, 18, 22, 20, 16, 14, 20, 14]
        for col, (h, w) in enumerate(zip(headers, col_widths)):
            ws.write(1, col, h, fmt['header'])
            ws.set_column(col, col, w)
        ws.set_row(1, 20)

        state_map = {
            'draft': 'Brouillon', 'assigned': 'Affecté',
            'maintenance': 'En maintenance', 'retired': 'Retiré'
        }

        for i, eq in enumerate(equipments):
            row = i + 2
            f = fmt['cell_alt'] if i % 2 else fmt['cell']
            fd = fmt['date_alt'] if i % 2 else fmt['date']
            fn = fmt['number_alt'] if i % 2 else fmt['number']

            ws.write(row, 0, i + 1, f)
            ws.write(row, 1, eq.name or '', f)
            ws.write(row, 2, eq.category_id.name if eq.category_id else '', f)
            ws.write(row, 3, eq.serial_number or '', f)
            ws.write(row, 4, eq.employee_id.name if eq.employee_id else '', f)
            ws.write(row, 5, eq.department_id.name if eq.department_id else '', f)
            ws.write(row, 6, eq.location or '', f)
            if eq.warranty_date:
                ws.write_datetime(row, 7,
                    datetime.datetime.combine(eq.warranty_date, datetime.time()), fd)
            else:
                ws.write(row, 7, '', f)
            ws.write(row, 8, eq.purchase_value or 0, fn)
            state_label = state_map.get(eq.state, eq.state)
            state_fmt = fmt['danger'] if eq.state == 'maintenance' else \
                        fmt['warning'] if eq.state == 'draft' else \
                        fmt['ok'] if eq.state == 'assigned' else fmt['cell']
            ws.write(row, 9, state_label, state_fmt)

        total_row = len(equipments) + 2
        ws.merge_range(total_row, 0, total_row, 7, 'TOTAL ÉQUIPEMENTS', fmt['total_label'])
        ws.write(total_row, 8, sum(equipments.mapped('purchase_value')), fmt['total'])
        ws.write(total_row, 9, len(equipments), fmt['total'])

        wb.close()
        output.seek(0)
        filename = f'inventaire_parc_{datetime.date.today().strftime("%Y%m%d")}.xlsx'
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )

    @http.route('/it_parc/export/couts_maintenance', type='http', auth='user')
    def export_couts_maintenance(self, **kwargs):
        output = io.BytesIO()
        wb, fmt = self._get_workbook_and_formats(output)
        ws = wb.add_worksheet('Coûts Maintenance')

        interventions = request.env['it.intervention'].search(
            [('state', '=', 'done')], order='equipment_id asc, date_start asc'
        )

        ws.merge_range('A1:H1',
            f'Synthèse des Coûts de Maintenance — {datetime.date.today().strftime("%d/%m/%Y")}',
            fmt['title'])
        ws.set_row(0, 24)

        headers = ['Équipement', 'Catégorie', 'Type', 'Technicien',
                   'Date début', 'Date fin', 'Durée (h)', 'Coût (FCFA)']
        col_widths = [28, 18, 14, 22, 14, 14, 12, 16]
        for col, (h, w) in enumerate(zip(headers, col_widths)):
            ws.write(1, col, h, fmt['header'])
            ws.set_column(col, col, w)
        ws.set_row(1, 20)

        type_map = {'corrective': 'Corrective', 'preventive': 'Préventive'}
        total_cost = 0
        total_hours = 0

        for i, inv in enumerate(interventions):
            row = i + 2
            f = fmt['cell_alt'] if i % 2 else fmt['cell']
            fd = fmt['date_alt'] if i % 2 else fmt['date']
            fn = fmt['number_alt'] if i % 2 else fmt['number']

            ws.write(row, 0, inv.equipment_id.name if inv.equipment_id else '', f)
            ws.write(row, 1, inv.equipment_id.category_id.name if inv.equipment_id.category_id else '', f)
            ws.write(row, 2, type_map.get(inv.type, inv.type), f)
            ws.write(row, 3, inv.technician_id.name if inv.technician_id else '', f)
            if inv.date_start:
                ws.write_datetime(row, 4, inv.date_start.replace(tzinfo=None), fd)
            else:
                ws.write(row, 4, '', f)
            if inv.date_end:
                ws.write_datetime(row, 5, inv.date_end.replace(tzinfo=None), fd)
            else:
                ws.write(row, 5, '', f)
            ws.write(row, 6, round(inv.duration_hours, 2), fn)
            ws.write(row, 7, inv.cost or 0, fn)
            total_cost += inv.cost or 0
            total_hours += inv.duration_hours or 0

        total_row = len(interventions) + 2
        ws.merge_range(total_row, 0, total_row, 5, 'TOTAL', fmt['total_label'])
        ws.write(total_row, 6, round(total_hours, 2), fmt['total'])
        ws.write(total_row, 7, total_cost, fmt['total'])

        wb.close()
        output.seek(0)
        filename = f'couts_maintenance_{datetime.date.today().strftime("%Y%m%d")}.xlsx'
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )

    @http.route('/it_parc/export/contrats_expirants', type='http', auth='user')
    def export_contrats_expirants(self, **kwargs):
        output = io.BytesIO()
        wb, fmt = self._get_workbook_and_formats(output)
        ws = wb.add_worksheet('Contrats Expirants')

        contrats = request.env['it.contrat'].search(
            [('state', '!=', 'renewed')], order='date_end asc'
        )
        contrats_60 = contrats.filtered(lambda c: 0 <= c.days_remaining <= 60)

        ws.merge_range('A1:G1',
            f'Contrats Expirant dans les 60 Jours — {datetime.date.today().strftime("%d/%m/%Y")}',
            fmt['title'])
        ws.set_row(0, 24)

        headers = ['Contrat', 'Fournisseur', 'Date début', 'Date fin',
                   'Jours restants', 'Montant (FCFA)', 'État']
        col_widths = [28, 24, 14, 14, 16, 18, 14]
        for col, (h, w) in enumerate(zip(headers, col_widths)):
            ws.write(1, col, h, fmt['header'])
            ws.set_column(col, col, w)
        ws.set_row(1, 20)

        for i, ct in enumerate(contrats_60):
            row = i + 2
            f = fmt['cell_alt'] if i % 2 else fmt['cell']
            fd = fmt['date_alt'] if i % 2 else fmt['date']

            ws.write(row, 0, ct.name or '', f)
            ws.write(row, 1, ct.partner_id.name if ct.partner_id else '', f)
            if ct.date_start:
                ws.write_datetime(row, 2,
                    datetime.datetime.combine(ct.date_start, datetime.time()), fd)
            else:
                ws.write(row, 2, '', f)
            if ct.date_end:
                ws.write_datetime(row, 3,
                    datetime.datetime.combine(ct.date_end, datetime.time()), fd)
            else:
                ws.write(row, 3, '', f)

            days = ct.days_remaining
            days_fmt = fmt['danger'] if days <= 7 else \
                       fmt['warning'] if days <= 30 else fmt['ok']
            ws.write(row, 4, days, days_fmt)
            ws.write(row, 5, ct.amount or 0, fmt['number'] if i % 2 == 0 else fmt['number_alt'])

            state_map = {'active': 'Actif', 'expired': 'Expiré', 'renewed': 'Renouvelé'}
            state_label = state_map.get(ct.state, ct.state)
            state_fmt = fmt['danger'] if ct.state == 'expired' else \
                        fmt['warning'] if ct.state == 'active' else fmt['ok']
            ws.write(row, 6, state_label, state_fmt)

        if not contrats_60:
            ws.merge_range(2, 0, 2, 6, 'Aucun contrat expirant dans les 60 prochains jours.', fmt['cell'])

        wb.close()
        output.seek(0)
        filename = f'contrats_expirants_{datetime.date.today().strftime("%Y%m%d")}.xlsx'
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )
