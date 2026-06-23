{
    'name': 'IT Parc - Gestion de Parc Informatique',
    'version': '18.0.1.0.0',
    'category': 'IT Management',
    'summary': 'Module de gestion de parc informatique pour TECHPARK CI',
    'description': """
        Module personnalisé pour TECHPARK CI - Gestion de parc informatique.
        Fonctionnalités :
        - Gestion des équipements avec workflow (Brouillon → Affecté → En maintenance → Retiré)
        - Affectation des équipements aux employés avec historique complet
        - Suivi des interventions de maintenance corrective et préventive
        - Gestion des contrats fournisseurs avec alertes d'expiration
        - Alertes automatiques pour garanties et contrats
        - Import en masse d'équipements via CSV
        - Rapports PDF (QWeb) et exports Excel (xlsxwriter)
        - Dashboard OWL pour la DSI
    """,
    'author': 'Ychrist (Yao Christ Uriel) - IIT Abidjan',
    'website': 'https://www.techpark.ci',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'stock',
        'purchase',
        'account',
        'maintenance',
        'web',
        'contacts',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/it_parc_demo.xml',
        'views/equipment_views.xml',
        'views/affectation_views.xml',
        'views/intervention_views.xml',
        'views/contrat_views.xml',
        'views/alerte_views.xml',
        'wizards/wizard_reaffectation_views.xml',
        'wizards/wizard_renouvellement_views.xml',
        'wizards/wizard_scan_alertes_views.xml',
        'wizards/wizard_import_csv_views.xml',
        'views/menus.xml',
        'views/dashboard_action.xml',
        'data/cron.xml',
        'report/report_fiche_equipement.xml',
        'report/report_inventaire.xml',
        'report/report_maintenances.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'it_parc/static/src/js/dashboard.js',
            'it_parc/static/src/xml/dashboard.xml',
            'it_parc/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
