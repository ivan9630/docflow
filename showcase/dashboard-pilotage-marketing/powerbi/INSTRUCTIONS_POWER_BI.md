# Assemblage dans Power BI Desktop

1. Exécuter `python pipeline.py` depuis la racine du projet.
2. Dans Power BI Desktop, importer les CSV `output/dim_*.csv` et `output/fact_performance.csv`.
3. Créer les quatre relations un-à-plusieurs entre les clés des dimensions et `fact_performance`.
4. Ajouter les mesures dans [mesures.dax](mesures.dax), avec le format **Pourcentage** pour CTR, ROI et taux de conversion.
5. Placer des cartes KPI (CTR, ROI, conversions), un histogramme par campagne, un tableau par segment et un filtre par canal.
6. Enregistrer sous `dashboard_pilotage.pbix` dans ce dossier.

Le dépôt contient les fichiers d'assemblage **mais pas un .pbix ou .pbit natif**. [Aperçu](../assets/dashboard_preview.svg) : maquette SVG calculée à partir des données fictives, et non capture de Power BI Desktop.
