# Validation — 23 septembre 2026

## Identité et périmètre
Dossier `proofs/it-lab`, dix modules indépendants, socle Python partagé. Révision exacte : commit GitHub contenant ce rapport. Aucun fichier de l’application DocuFlow modifié.

## Résultats observés
- **PROVEN** : 34 tests réussis sous Python 3.13.2 / Windows, après correction des connexions SQLite non fermées.
- Commande : `python -W error::ResourceWarning -m unittest discover -s tests -v` ; résultat `Ran 34 tests ... OK`, sans avertissement.
- Dix exécutions CLI réelles, comparaison des sorties JSON à l’appel métier et absence de mutation des entrées.
- Cas limites : doubles identifiants, liens invalides, tests en attente, types invalides, valeurs non finies, dates sans fuseau/futures, rejets ETL, MAD nulle, jointures multipliantes, graphe cyclique, stock insuffisant, transitions interdites et écart de facture.
- Tests HTTP réels sur boucle locale : création de ticket, lecture SQL, erreurs 400/404 et retour HTML.
- **PROVEN** : parcours navigateur local « saisir un incident → Créer → Ticket créé → ticket affiché », puis rechargement et ticket toujours présent. Rendu étroit inspecté, libellés lisibles.
- **PROVEN** : entrées et code destinés à la publication inspectés ; données synthétiques, aucune clé API ni coordonnées privées.

## Corrections issues de l’autocritique
Les context managers SQLite ne fermaient pas les connexions : utilisation explicite de `contextlib.closing`, puis réexécution complète. La mémoire SQLite du serveur HTTP est fermée à l’arrêt.

## Limites, sans crédit indu
- Compatibilité Python 3.11 annoncée par les API employées, mais exécution effective réalisée uniquement sous 3.13.2.
- Pas de déploiement public du serveur, de test de charge, d’audit sécurité complet ni d’intégration aux SI d’employeurs.
- Pas de validation Power BI, Sage X3, BEXT, React, Java, matériel réseau ou modèle ML entraîné.
- Tests ciblés, pas de garantie d’absence de tout défaut ; l’objectif est une démonstration reproductible, pas un produit prêt pour la production.
- La maîtrise et la capacité d’explication autonome par l’auteur ne sont pas évaluées par cette suite.

## Rejouer
Depuis ce dossier : `python -W error::ResourceWarning -m unittest discover -s tests -v`.
Pour le navigateur : `python run.py service-desk-web --serve`, ouvrir http://127.0.0.1:8765, saisir un incident fictif, créer, puis recharger.

