# Rapprochement stocks et factures

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Support ERP

Rejouer un journal de stock et détecter les écarts de montants des factures fictives.

**Techniques réellement présentes :** Python, règles métier, validation, rapprochement, montants en centimes.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py erp-reconciliation
python run.py erp-reconciliation erp-reconciliation/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** Stock final SKU1 : 12 ; facture F1 : écart -100 centimes.

## Contrôle et limites

Aucun connecteur Sage X3, Crystal Reports ou écriture comptable ; calcul net hors taxes sans conversion de devise.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi rejeter un mouvement qui rend le stock négatif au lieu de masquer l’anomalie ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

