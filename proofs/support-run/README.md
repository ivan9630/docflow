# Démonstrateur support applicatif / RUN — DocuFlow

Exercice personnel créé avec assistance IA, septembre 2026. Module isolé : aucun changement du fonctionnement de DocuFlow. Ce n'est ni une réalisation client ni un outil de production.

## Cas concret
Un traitement documentaire dépend de son API, sa base, sa file de messages, ses workers et son stockage. À partir d'un relevé **synthétique**, le script valide les données, propose une priorité d'incident et ordonne les vérifications. Il distingue une panne de worker d'une panne de dépendance, sans affirmer connaître la cause racine.

## Reproduire sans compte ni dépense
Python 3.11+ ; uniquement la bibliothèque standard. Depuis ce dossier :

```sh
python -m unittest -v
python diagnose.py sample.json
```

Créer `sample.json` avec ce contenu de démonstration :

```json
{"api": true, "database": true, "queue": false, "worker": false, "storage": true}
```

Résultat attendu : priorité P2, vérification de la queue avant le worker, puis collecte de preuves expurgées et escalade. Les priorités sont des conventions de cet exercice, pas des SLA contractuels.

## Preuves et limites
Tests : état sain, API indisponible, worker indisponible, dépendances, clé absente, types incorrects, non-mutation, exécution réelle de la commande avec entrée valide et JSON invalide. Aucun secret, réseau, redémarrage ni suppression.

Ce module démontre Python, JSON, validation, tests de régression, procédure de diagnostic et documentation. Il ne démontre PAS l'administration de Windows/Active Directory, un déploiement Docker, une supervision réelle ou la disponibilité de la pile DocuFlow. Les snapshots ne sont pas des mesures en direct.

## Présenter et comprendre en entretien
1. Expliquer pourquoi `"false"` est refusé alors que `false` est accepté.
2. Rejouer le cas queue + worker et justifier l'ordre des vérifications.
3. Montrer le test de commande, distinguer test unitaire et intégration CLI.
4. Expliquer les limites : sans logs ni horodatage, pas de diagnostic causal fiable.
5. Suite possible : collecte réelle autorisée, horodatage, timeouts et métriques ; elle n'est pas implémentée ici.

Ne présenter ce travail comme une compétence acquise qu'après l'avoir exécuté et compris. Formulation CV honnête : « Démonstrateur personnel de diagnostic applicatif : validation JSON, triage de dépendances et tests automatisés Python sur scénarios synthétiques. »
