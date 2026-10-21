# Data & Document Lab — démonstrateurs interactifs

Quatre cas personnels, interactifs et sans dépendance externe applicative :

1. **Reprise documentaire** — contrôles de schéma, typologie cible, champs obligatoires, identifiants doublonnés et mise en évidence des exceptions.
2. **Workflow d’expertise** — machine à états avec transitions métier et historique des validations.
3. **Pilotage de charge** — comparaison déterministe demande/capacité, écarts et lecture des périodes sous tension.
4. **Pipeline analytique** — validation d’un petit jeu synthétique, déduplication et agrégations de médailles par pays.

Les pages de démonstration sont exécutées côté navigateur et n’envoient aucune donnée. Les exemples sont inventés, en petit volume et sans données d’employeur. Aucun lien technique à OpenText/Documentum, Power BI, React, AWS ou à un système EDF/GRTgaz n’est revendiqué. Ces prototypes ne prouvent pas qu’une migration réelle, un modèle prédictif entraîné ou un déploiement en entreprise a été réalisé.

## Voir la démo

Après publication GitHub Pages : `https://ivan9630.github.io/docflow/` (la publication est pilotée par `.github/workflows/portfolio-live-pages.yml`).

La démo Web utilise JavaScript natif et fonctionne dans le navigateur. Les scripts reproductibles dans `engine/` utilisent Python standard et SQLite ; ils donnent un second angle vérifiable sur les règles métier. Aucun de ces exemples ne constitue une intégration réelle à Documentum, Power BI, EDF ou aux Jeux Olympiques.

Pour lancer les tests et la démo localement, ouvrir un terminal dans ce dossier puis :

```bash
npm test
npm run test:python
npm run serve
```

Ouvrir ensuite `http://localhost:4173`. Python 3 est nécessaire pour le serveur statique, Node.js 18+ uniquement pour les tests. Le code applicatif du navigateur utilise la plateforme web standard.

## Tests et limites

`npm test` vérifie les règles métier JavaScript ; `npm run test:python` vérifie les fonctions Python et le pipeline SQLite. Le dataset olympique est totalement synthétique. L’échantillon documentaire est pédagogique ; il n’effectue aucune requête DQL/SQL vers Documentum, aucune écriture DMS ni export chez un employeur.
