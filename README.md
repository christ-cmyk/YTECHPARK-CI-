# it_parc — Module Odoo 18 Enterprise
## Gestion de parc informatique — TECHPARK CI

### Description
Module Odoo 18 Enterprise personnalisé pour la gestion complète du parc
informatique interne : équipements, affectations, interventions,
contrats fournisseurs, alertes automatiques, rapports PDF, exports Excel
et tableau de bord OWL temps réel.

### Prérequis
- Odoo 18 Enterprise
- Python 3.11+
- xlsxwriter : `pip install xlsxwriter`

### Installation
1. Copier le dossier `it_parc/` dans le répertoire `addons/` d'Odoo
2. Vérifier que `addons_path` dans `odoo.conf` pointe vers ce dossier
3. Mettre à jour le module :
```
python odoo-bin -c odoo.conf -u it_parc -d <votre_base>
```
4. Dans Odoo : Apps → Rechercher `it_parc` → Installer

### Fonctionnalités
| # | Fonctionnalité | Description |
|---|---------------|-------------|
| F01 | Équipements | Workflow 4 états : Brouillon → Affecté → Maintenance → Retiré |
| F02 | Affectations | Historique complet par équipement avec wizard de réaffectation |
| F03 | Interventions | Suivi corrective/préventive, durée auto, vue calendrier |
| F04 | Contrats | Suivi fournisseurs, jours restants, wizard renouvellement avec blocage 5j |
| F05 | Licences logicielles | Gestion des licences par équipement, type, expiration |
| F06 | Alertes | Scan auto (ir.cron) + scan manuel, garanties et contrats |
| F07 | Snapshots inventaire | Capture instantanée de l'état du parc avec historique |
| F08 | Import CSV | Chargement en masse, détection doublons, rapport d'import |
| F09 | Rapports PDF | 4 rapports QWeb : fiche équipement, inventaire, maintenances, reçu contrat |
| F10 | Exports Excel | 3 exports xlsxwriter avec couleurs conditionnelles |
| F11 | Dashboard OWL | IT Command Center : 4 KPIs, donut chart, barres, alertes |

### Groupes de sécurité
| Groupe | Droits |
|--------|--------|
| IT Technicien | Lecture sur tout + CRU sur interventions |
| IT Manager | Accès complet CRUD sur tous les modèles |

### Structure des fichiers
```
it_parc/

├── __init__.py
├── __manifest__.py
├── README.md
├── models/          # 7 modèles Python (equipment, affectation, intervention, contrat, alerte, licence, inventaire_snapshot)
├── views/           # Vues XML + menus + action dashboard
├── wizards/         # 6 wizards (réaffectation, renouvellement, scan alertes, import CSV, rapport inventaire, rapport maintenances)
├── report/          # 4 rapports QWeb PDF
├── security/        # Groupes + ACLs
├── data/            # Cron + données démo
├── controllers/     # Exports Excel (HTTP) + dashboard (JSON-RPC)
└── static/src/      # Dashboard OWL (js, xml, scss)
```

### Exports Excel
Accessibles via **IT Parc → Exports Excel** (IT Manager uniquement) :
- Inventaire complet → `/it_parc/export/inventaire`
- Synthèse coûts maintenance → `/it_parc/export/couts_maintenance`
- Contrats expirants 60j → `/it_parc/export/contrats_expirants`

### Auteur
Ychrist (Yao Christ Uriel) — Étudiant L2 Informatique, IIT Abidjan
Projet académique — Juin 2026
