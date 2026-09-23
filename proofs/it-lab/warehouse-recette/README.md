# Recette d’un workflow logistique

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — AMOA / recette WMS

Tester réservation, préparation, expédition et annulation avec un stock synthétique.

**Techniques réellement présentes :** Python, machine à états, tests d’acceptation, anomalies.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py warehouse-recette
python run.py warehouse-recette warehouse-recette/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** 4 scénarios acceptés, y compris deux rejets attendus.

## Contrôle et limites

Modèle pédagogique sans intégration à BEXT/WMS. Stock disponible uniquement ; ni concurrence ni persistance multi-commandes.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Comment distinguer un rejet attendu d’un échec de test ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

