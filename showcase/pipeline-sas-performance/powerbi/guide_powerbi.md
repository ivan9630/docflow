# Guide Power BI Desktop : dashboard opérationnel et stratégique

Le dépôt inclut le schéma, les CSV, les requêtes et les mesures DAX, mais ne revendique pas de fichier .pbix natif créé dans Power BI Desktop.

1. Depuis la racine du projet, lancer : python python/pipeline_marketing.py
2. Dans Power BI Desktop, importer les fichiers output/fact_campagnes.csv et output/dim_*.csv (un fichier par dimension).
3. Dans Modèle, créer les relations 1 -> plusieurs de dim_region, dim_secteur, dim_campagne, dim_segment, dim_canal, dim_semaine vers fact_campagnes via les clés *_id. Filtrage dans un seul sens.
4. Ajouter les mesures listées dans mesures.dax individuellement, et mettre les ratios en format Pourcentage.

## Pages de rapports
- **Direction / pilotage stratégique** : cartes d'impressions, contacts, rendez-vous, CTR, coût/RDV et variation nationale; graphique hebdomadaire.
- **Réseau / pilotage opérationnel** : matrice Région × Secteur et filtres Région, Canal, Campagne; rang des campagnes et écarts au national.
- **Marketing / étude d'impact** : entonnoir Impressions → Clics → Contacts → RDV; exposés/témoins avant/après et indicateur DiD.
- **Fiabilité et qualité** : 605 lignes d'origine, 5 rejets, 600 retenues, motifs et audit.

## Interprétation
Le CTR, le taux de contact et les autres ratios sont calculés comme des rapports de sommes, et non des moyennes de taux.
Les données sont synthétiques; il n'existe aucun accès à une base réelle de France Travail.
Le coefficient DiD reste descriptif et ne démontre pas un lien causal.

Voir aussi le tableau de bord HTML autonome (généré à partir des données du projet) dans output.
