# Qualité de données et reporting

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Data analyst

Rejeter doublons et montants invalides avant agrégation par équipe de dossiers entièrement fictifs.

**Techniques réellement présentes :** Python, ETL, SQLite, SQL GROUP BY, contrôles qualité.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py claims-reporting
python run.py claims-reporting claims-reporting/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** 2 lignes acceptées, 2 rejetées ; équipe A : 200 euros, délai moyen 3 jours.

## Contrôle et limites

Pas de fichier Power BI, VBA ou SAS ; indicateurs simples, montants REAL non adaptés à une comptabilité précise.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi conserver les rejets plutôt que corriger silencieusement les montants ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

