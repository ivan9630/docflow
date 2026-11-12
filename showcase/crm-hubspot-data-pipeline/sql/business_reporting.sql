-- Tableaux de bord commerciaux basés sur la base SQLite générée.
-- Performance par source : dénominateurs explicites.
SELECT ds.source, COUNT(*) AS leads,
       SUM(fl.contacts_livres) AS volumes_livres,
       SUM(fl.contacts_convertis) AS transformations,
       ROUND(100.0*SUM(fl.contacts_convertis)/NULLIF(SUM(fl.contacts_livres),0),2) AS taux_transformation_pct,
       ROUND(SUM(fl.cout_acquisition)/NULLIF(COUNT(*),0),2) AS cout_par_lead_eur,
       ROUND(SUM(fl.ca_facture-fl.cout_acquisition),2) AS marge_eur,
       SUM(fl.litiges) AS litiges
FROM fact_leads fl JOIN dim_source ds ON ds.source_id=fl.source_id
GROUP BY ds.source ORDER BY marge_eur DESC;

-- CRM et facturation : écarts à investiguer.
SELECT lead_id,entreprise,email,ca_facture,montant_facture,ecart_facturation
FROM fact_leads WHERE ABS(ecart_facturation)>0.01
ORDER BY ABS(ecart_facturation) DESC;

-- Segmentation pour les équipes : score qualité, priorité.
SELECT segment, COUNT(*) AS leads,ROUND(AVG(score_qualite),1) AS score_qualite_moyen,
       ROUND(AVG(score_conversion_ml),1) AS score_ml_moyen
FROM fact_leads GROUP BY segment ORDER BY score_ml_moyen DESC;
