/** @odoo-module **/
import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

class ItParcDashboard extends Component {
    static template = "it_parc.ItParcDashboard";

    setup() {
        this.state = useState({
            loading: true,
            currentDate: new Date().toLocaleDateString('fr-FR', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
            }),
            data: {
                total_eq: 0,
                eq_this_quarter: 0,
                maintenance_count: 0,
                maintenance_pct: 0,
                alertes_open: 0,
                alertes_warranty: 0,
                alertes_contract: 0,
                total_cost: 0,
                states: { draft: 0, assigned: 0, maintenance: 0, retired: 0 },
                categories: [],
                alertes_list: [],
                sites_list: [],
                immobilisation_pct: 0,
            },
        });
        onMounted(() => this.loadData());
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await rpc("/it_parc/dashboard/data", {});
            this.state.data = data;
        } catch (e) {
            console.error("Erreur chargement dashboard it_parc :", e);
        } finally {
            this.state.loading = false;
        }
    }

    formatCost(value) {
        if (!value) return "0";
        if (value >= 1000000) return (value / 1000000).toFixed(1) + "M";
        if (value >= 1000) return (value / 1000).toFixed(0) + "K";
        return value.toLocaleString('fr-FR');
    }

    barWidth(count) {
        const max = Math.max(...(this.state.data.categories.map(c => c.count) || [1]));
        return max > 0 ? Math.round((count / max) * 100) : 0;
    }

    barColor(index) {
        const colors = ['#378ADD', '#1D9E75', '#7F77DD', '#EF9F27', '#D85A30', '#E24B4A'];
        return colors[index % colors.length];
    }

    siteColor(index) {
        const colors = ['#378ADD', '#1D9E75', '#7F77DD', '#EF9F27'];
        return colors[index % colors.length];
    }
}

registry.category("actions").add("it_parc.dashboard_action_client", ItParcDashboard);

export default ItParcDashboard;
