# IT Lab — dix démonstrateurs techniques

Dix mini-projets personnels réalisés avec assistance IA le 23 septembre 2026. Ils illustrent des cas concrets de support informatique, AMOA, développement, data et ERP. **Ce ne sont pas des expériences professionnelles.** Données intégralement synthétiques, sans données d’employeurs, coordonnées privées ni services payants.

Modules autonomes sur le plan métier ; petit socle partagé de validation et d’exécution. Aucun changement à l’application DocuFlow. Python 3.11+ et bibliothèque standard uniquement.

| Projet | Compétences démontrées |
|---|---|
| [Traçabilité besoins → recette](requirements-traceability) | Python, JSON, critères d’acceptation, couverture de recette |
| [Audit de parc hors ligne](workstation-audit) | Python, validation d’inventaire, diagnostic, documentation |
| [Triage N1 et escalade](incident-triage) | Python, dates avec fuseaux, priorisation, SLA |
| [Qualité de données et reporting](claims-reporting) | Python, ETL, SQLite, SQL GROUP BY, contrôles qualité |
| [Détection explicable d’écarts](transaction-alerts) | Python, médiane, MAD, validation, scoring explicable |
| [Mini Service Desk web](service-desk-web) | Python, HTTP REST, SQLite, HTML, JavaScript, validation, tests d’intégration |
| [Indicateurs retail SQL](retail-bi) | Python, SQLite, CTE SQL, grain des données, indicateurs |
| [Diagnostic de dépendances réseau](network-path) | Python, validation IP, graphe orienté, tri topologique |
| [Recette d’un workflow logistique](warehouse-recette) | Python, machine à états, tests d’acceptation, anomalies |
| [Rapprochement stocks et factures](erp-reconciliation) | Python, règles métier, validation, rapprochement, montants en centimes |

## Reproduire

Depuis ce dossier :

```sh
python -m unittest discover -s tests -v
python run.py retail-bi
python run.py transaction-alerts transaction-alerts/sample.json
python run.py service-desk-web --serve
```

Le dernier exemple expose uniquement http://127.0.0.1:8765 ; arrêter avec Ctrl+C. Aucun projet n’exige AWS, une clé API ou un compte SaaS. Les exemples ne font aucun appel externe. Les tests HTTP démarrent temporairement un serveur local sur un port libre.

Chaque dossier contient code, données d’exemple, explication, résultats attendus et limites. Le [rapport de validation](VALIDATION.md) distingue les tests réellement exécutés des vérifications non réalisées.

## Utilisation honnête en candidature

Choisir le module pertinent, l’exécuter et le comprendre avant d’en parler. Mention possible : « Projet personnel assisté par IA — [nom] : [techniques effectivement implémentées], cas synthétiques et tests automatisés. » Ne pas revendiquer un déploiement client, une maîtrise de Sage X3/Power BI/React/Java, ou une performance ML à partir de ces seuls exercices.

Le serveur web est pédagogique : ni authentification ni persistance disque, ne pas l’exposer sur Internet. Les autres modules sont des analyses hors ligne. Les seuils de priorité et d’anomalie sont des conventions d’exercice. Aucune licence du dépôt n’est modifiée par ce dossier.

