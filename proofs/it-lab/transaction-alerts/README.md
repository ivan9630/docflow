# Détection explicable d’écarts

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Python / data science

Comparer des transactions fictives à un historique distinct et produire des alertes à examiner.

**Techniques réellement présentes :** Python, médiane, MAD, validation, scoring explicable.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py transaction-alerts
python run.py transaction-alerts transaction-alerts/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** TX1 sans alerte ; TX2 à examiner ; médiane 100 et MAD 1.

## Contrôle et limites

Baseline statistique non entraînée : ce n’est ni un modèle ML validé ni un détecteur de fraude/AML. Aucun taux de performance sans données étiquetées.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Comment choisir un seuil et mesurer les faux positifs sur des données étiquetées ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

