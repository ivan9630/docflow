# AI Governance Lab — prototype d'audit IA

Mini-projet personnel (Python, bibliothèque standard) conçu pour illustrer une démarche de **diagnostic de cas d'usage IA**, gouvernance des données et gestion des risques. Ce n'est ni un audit juridique, ni une certification de conformité RGPD/AI Act.

## Fonctionnalités
- Lecture d'un portefeuille de cas d'usage IA au format JSON.
- Questionnaire simple : données personnelles/sensibles, exposition publique, décisions à impact, fournisseur tiers, supervision humaine.
- Détection indicative d'e-mails et de numéros de téléphone dans un extrait de texte.
- Score de priorisation transparent et plan d'actions explicable pour chaque cas.
- Exports : tableau CSV, rapport Markdown, résultats JSON.
- Tests unitaires sans dépendance externe.

## Démarrage
\`\`\`bash
python3 app.py --input examples/use_cases.json --output out
python3 -m unittest discover -s tests -v
\`\`\`
Ouvrez \`out/report.md\` et \`out/risk_register.csv\`.

## Démonstration / entretien
1. Définir le cas d'usage, ses utilisateurs et son périmètre de données.
2. Identifier les risques prioritaires et les contrôles manquants.
3. Proposer un atelier métier / DPO / sécurité et un plan de mesures.
4. Réévaluer le dossier après mise en place de la supervision et des contrôles.

## Périmètre et limites
Les poids du score sont **des hypothèses pédagogiques**, pas une classification légale des risques au sens de l'AI Act. Les regex de données personnelles sont approximatives et ne détectent pas toutes les PII. Les données fournies en exemple sont entièrement fictives. Aucun appel externe ni traitement en ligne.
