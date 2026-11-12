# SAS Pilotage Performance — Data Analyst / BI

Projet personnel d'Ivan TCHOMTE : fiabiliser des données de campagnes fictives et produire des indicateurs de pilotage territoriaux.

**Le code SAS n'a pas encore été exécuté sur SAS Studio.** La validation indépendante a été faite en Python sur le jeu fictif généré avec la même graine.

## Cas d'usage

- 605 interactions fictives, dont 1 doublon et 4 lignes invalides ; 600 observations valides.
- Détecter les doublons, les agences inconnues, les compteurs incohérents.
- Exploiter des données par région/canal, calculer CTR, taux de rendez-vous et coût par rendez-vous.
- Synthétiser des données de pilotage pour des tableaux de bord.

## Structure
- \`generate.py\` : création de 3 CSV de données synthétiques
- \`sas/01_pipeline.sas\` : DATA step, PROC SORT, PROC SQL, contrôles de qualité, macro %kpis, PROC REPORT / SGPLOT, ODS HTML, exports CSV
- \`validation/verify_dataset.py\` : vérification indépendante (nécessite pandas)

## Démarrage
1. \`python generate.py\`
2. Copier le dossier dans SAS Studio et créer un sous-dossier \`outputs\`.
3. Remplacer \`%let SAS_ROOT=...\` dans le programme SAS par le chemin réel.
4. Exécuter \`sas/01_pipeline.sas\`.
5. Comparer \`outputs/kpi_region.csv\` au rapport généré par \`python validation/verify_dataset.py\`.

Pour une **démo HTML interactive déjà calculée**, télécharger le dossier complet depuis la candidature. Ce dépôt contient le code reproductible.

**Données purement fictives.** Aucune donnée interne de France Travail ou d'un employeur. Résultats SAS non testés dans un moteur SAS avant publication. Licence MIT.