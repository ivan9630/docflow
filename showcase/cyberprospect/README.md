# CyberProspect — démonstrateur SDR IT & cybersécurité

Prototype personnel de qualification B2B : enrichissement de comptes, signaux d'achat, priorisation de prospects et suivi de campagnes. **Aucun contact réel** : les données sont fictives, l'outil n'envoie ni e-mail ni messages LinkedIn.

## Fonctionnalités
- Chargement et dédoublonnage des contacts CRM depuis CSV.
- Scoring explicable selon secteur IT, taille de l'entreprise, signaux NIS2 / recrutement cyber / nouveau RSSI, et qualité des coordonnées.
- Segmentation et file de relance, brouillons de messages personnalisés non envoyés.
- Export CSV des prospects classés et synthèse Markdown des KPIs.
- Tests automatisés (unittest) avec la bibliothèque standard Python.

## Lancer
```bash
python3 app.py --contacts examples/contacts.csv --output out
python3 -m unittest discover -s tests -v
```
Puis consulter `out/qualified.csv`, `out/messages_draft.csv` et `out/report.md`.

## Cas d'usage présenté en entretien
1. Définition d'une cible (DSI, RSSI, responsables IT).
2. Recherche de signaux d'achat pertinents et récents.
3. Qualification et priorisation des prospects.
4. Rédaction d'une approche personnalisée, revue humaine.
5. Suivi des réponses et des prochaines actions dans le CRM.

Ce prototype ne prétend pas détecter automatiquement des incidents de sécurité ou vérifier les obligations NIS2. Il n'effectue aucun scraping, appel réseau ni prospection automatisée. Une campagne réelle nécessiterait une base légale, des contrôles RGPD et une gestion de l'opposition.
