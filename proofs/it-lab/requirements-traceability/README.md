# Traçabilité besoins → recette

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — AMOA

Relier chaque exigence à des tests et distinguer absence de test, échec et test non exécuté.

**Techniques réellement présentes :** Python, JSON, critères d’acceptation, couverture de recette.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py requirements-traceability
python run.py requirements-traceability requirements-traceability/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** R1 accepté ; R2 en attente ; livraison non prête.

## Contrôle et limites

Ce moteur vérifie des statuts déclarés, pas une application métier. Les preuves des tests fonctionnels doivent encore être jointes.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi une exigence sans test ne doit-elle pas être acceptée ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

