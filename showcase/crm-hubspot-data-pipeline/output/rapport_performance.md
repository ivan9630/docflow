# Rapport de pilotage CRM — démonstration

## Audit et qualité
- **260 contacts** en entrée ; **12 doublons** et **8 anomalies** rejetés ; **240 contacts uniques fiabilisés**.
- Taux de dédoublonnage : **4.62 %** des lignes sources. Taux de rejet total : **7.69 %**.
- Score qualité moyen : **91.44 / 100** ; **3 segments** de priorité.
- **240 contacts** qualifiés automatiquement. **8 écarts de facturation** signalés.

## Pilotage commercial
- **3083 contacts livrés**, **761 transformations** et **15 litiges** (simulés).
- Coût d'acquisition moyen par lead : **150.98 €**.
- ML supervisé : ROC-AUC **0.715** et balanced accuracy **0.655**, sur **60 observations de test synthétiques**. Aucun score mesuré sur CRM réel.

## Recommandations pour le pilotage
1. Examiner les sources dont le taux de conversion est faible avant ajustement budgétaire.
2. Prioriser les segments élevés tout en imposant une validation métier et un contrôle de conformité.
3. Traiter les anomalies détectées et rapprocher les lignes présentant des écarts entre facturation et revenus.
4. Contrôler les filtres client avant export ; ne pas automatiser l'envoi externe sans accord, logs et règles de confidentialité.

**Données de démonstration uniquement.** Les valeurs ne reflètent aucun résultat d'entreprise.
