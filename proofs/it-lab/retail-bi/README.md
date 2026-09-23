# Indicateurs retail SQL

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Business Intelligence

Calculer chiffre d’affaires en centimes, stock et références en rupture sans multiplier les stocks lors des jointures.

**Techniques réellement présentes :** Python, SQLite, CTE SQL, grain des données, indicateurs.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py retail-bi
python run.py retail-bi retail-bi/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** books : 5000 centimes, 4 unités en stock, 1 référence en rupture.

## Contrôle et limites

Prix de catalogue supposés fixes sur la période ; aucun outil BI ou cloud déployé, pas de calcul des retours/remises.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi agréger les ventes avant la jointure au catalogue ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

