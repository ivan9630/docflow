# Diagnostic de dépendances réseau

Projet personnel de démonstration réalisé avec assistance IA le 23 septembre 2026. Données fictives uniquement ; aucun travail client, partenariat ou résultat de production revendiqué.

## Cas d’usage — Support réseaux

Ordonner les vérifications à partir d’un instantané réseau fictif et refuser les dépendances cycliques.

**Techniques réellement présentes :** Python, validation IP, graphe orienté, tri topologique.

## Exécuter

Python 3.11+, aucune dépendance tierce. Depuis `proofs/it-lab` :

```sh
python run.py network-path
python run.py network-path network-path/sample.json
python -m unittest discover -s tests -v
```

Le fichier `sample.json` constitue une entrée reproductible. La commande écrit un rapport JSON sur la sortie standard ; une entrée invalide provoque un code retour 2. Aucune donnée réelle à saisir.

**Résultat attendu :** Vérifier gateway, puis switch, puis workstation.

## Contrôle et limites

Aucun scan, ping, pare-feu ou matériel réel. Les IP 192.0.2.0/24 sont réservées à la documentation. Aucun diagnostic causal certain.

Les tests communs couvrent l’entrée d’exemple, l’absence de mutation et l’exécution CLI ; des tests dédiés vérifient les règles et erreurs propres à ce module. Voir [la suite](../tests/test_projects.py) et [le rapport](../VALIDATION.md).

## Préparer l’entretien

1. Exécuter le cas fourni et expliquer chaque résultat.
2. Modifier un cas limite, prédire la sortie et relancer les tests.
3. Répondre : Pourquoi trois équipements injoignables ne signifient-ils pas trois pannes indépendantes ?
4. Expliquer les limites ci-dessus et une amélioration possible sans la présenter comme déjà réalisée.

Ce code est une base de travail personnelle assistée par IA, pas une preuve de maîtrise autonome avant appropriation.

