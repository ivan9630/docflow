# Audit de parc hors ligne

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Support poste de travail

Prioriser les contrôles d’espace disque, mémoire et chiffrement sur un inventaire synthétique Windows/macOS.

**Techniques réellement présentes :** Python, validation d’inventaire, diagnostic, documentation.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py workstation-audit
python run.py workstation-audit workstation-audit/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** Deux appareils à examiner, sans suppression ni modification système.

## Contrôle et limites

Aucune collecte réelle Windows/macOS, aucune administration AD/GPO ; seuils propres à l’exercice.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi ne pas supprimer automatiquement des fichiers en cas de disque plein ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

