# Mini Service Desk web

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Développement full-stack

Créer et consulter des tickets fictifs via une interface web et une API locale.

**Techniques réellement présentes :** Python, HTTP REST, SQLite, HTML, JavaScript, validation, tests d’intégration.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py service-desk-web
python run.py service-desk-web service-desk-web/sample.json
python -m unittest discover -s tests -v
```

Interface locale : `python run.py service-desk-web --serve`, puis ouvrir http://127.0.0.1:8765. Ctrl+C pour arrêter. La base est réinitialisée à chaque lancement.

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** POST /api/tickets : 201 ; GET restitue le ticket enregistré en SQLite mémoire.

## Contrôle et limites

Pas de React ni Java. Pas d’authentification, TLS ou persistance disque : strictement local, non destiné à la production.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi des requêtes SQL paramétrées et textContent dans le navigateur ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

