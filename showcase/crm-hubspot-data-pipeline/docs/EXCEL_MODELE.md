# Tableurs avancés — Excel / Google Sheets

Les fichiers `output/kpi_source.csv`, `output/kpi_segment.csv` et `output/kpi_secteur.csv` sont utilisables dans Excel ou Google Sheets. Pour un suivi régulier :

- Importer `output/contacts_fiabilises_scores.csv` comme table **Contacts**.
- Ajouter un tableau croisé dynamique Source × Statut ou Segment × Secteur.
- Utiliser `NB.SI.ENS` / `COUNTIFS`, `SOMME.SI.ENS` / `SUMIFS` et les filtres sur la date pour les volumes et les coûts.
- Calculer **taux de transformation** = `SOMME(contacts_convertis) / SOMME(contacts_livres)` (et non moyenne des ratios de chaque ligne).
- Utiliser une mise en forme conditionnelle pour mettre en évidence les écarts de facturation et scores qualité faibles.
- Rapprocher les métriques du tableur des requêtes dans `sql/business_reporting.sql` ; documenter toute différence de périmètre.

Ces fonctionnalités sont documentées comme **procédure** ; elles ne sont pas revendiquées comme une connexion réelle à HubSpot.
