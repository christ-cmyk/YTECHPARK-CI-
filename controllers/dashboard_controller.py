import datetime
from odoo import http
from odoo.http import request


class ItParcDashboardController(http.Controller):

    @http.route('/it_parc/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, **kwargs):
        today = datetime.date.today()
        Equipment = request.env['it.equipment']
        Intervention = request.env['it.intervention']
        Alerte = request.env['it.alerte']
        Contrat = request.env['it.contrat']

        total_eq = Equipment.search_count([])
        eq_this_quarter = Equipment.search_count([
            ('purchase_date', '>=', (today - datetime.timedelta(days=90)).strftime('%Y-%m-%d'))
        ])

        maintenance_count = Equipment.search_count([('state', '=', 'maintenance')])
        maintenance_pct = round((maintenance_count / total_eq * 100), 1) if total_eq else 0

        alertes_open = Alerte.search_count([('state', '=', 'open')])
        alertes_warranty = Alerte.search_count([('state', '=', 'open'), ('type', '=', 'warranty')])
        alertes_contract = Alerte.search_count([('state', '=', 'open'), ('type', '=', 'contract')])

        interventions_done = Intervention.search([('state', '=', 'done')])
        total_cost = sum(interventions_done.mapped('cost'))

        states = {
            'draft': Equipment.search_count([('state', '=', 'draft')]),
            'assigned': Equipment.search_count([('state', '=', 'assigned')]),
            'maintenance': Equipment.search_count([('state', '=', 'maintenance')]),
            'retired': Equipment.search_count([('state', '=', 'retired')]),
        }

        categories = []
        cats = request.env['it.equipment.category'].search([])
        for cat in cats:
            count = Equipment.search_count([('category_id', '=', cat.id)])
            if count > 0:
                categories.append({'name': cat.name, 'count': count})
        categories.sort(key=lambda x: x['count'], reverse=True)

        alertes_list = []
        alertes = Alerte.search([('state', '=', 'open')], order='date_expiry asc', limit=5)
        for a in alertes:
            days = a.days_before
            alertes_list.append({
                'name': a.name,
                'days_before': days,
                'type': a.type,
                'urgency': 'urgent' if days <= 7 else 'warning' if days <= 30 else 'ok',
                'date_expiry': a.date_expiry.strftime('%d/%m/%Y') if a.date_expiry else '',
            })

        sites = {}
        all_eq = Equipment.search([])
        for eq in all_eq:
            loc = eq.location or 'Non défini'
            sites[loc] = sites.get(loc, 0) + 1
        sites_list = sorted(
            [{'name': k, 'count': v} for k, v in sites.items()],
            key=lambda x: x['count'], reverse=True
        )

        return {
            'total_eq': total_eq,
            'eq_this_quarter': eq_this_quarter,
            'maintenance_count': maintenance_count,
            'maintenance_pct': maintenance_pct,
            'alertes_open': alertes_open,
            'alertes_warranty': alertes_warranty,
            'alertes_contract': alertes_contract,
            'total_cost': total_cost,
            'states': states,
            'categories': categories[:6],
            'alertes_list': alertes_list,
            'sites_list': sites_list[:4],
            'immobilisation_pct': maintenance_pct,
        }
