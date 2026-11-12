-- Requêtes métier sur la base output/pilotage_campagnes.sqlite.
-- Synthèse nationale.
SELECT SUM(impressions) AS impressions, SUM(clics) AS clics,
 ROUND(100.0*SUM(clics)/NULLIF(SUM(impressions),0),2) AS ctr_pct,
 SUM(rdv) AS rdv, ROUND(SUM(cout_eur)/NULLIF(SUM(rdv),0),2) AS cout_par_rdv_eur
FROM fact_campagnes;

-- Suivi local et comparaison entre régions.
SELECT r.region, COUNT(*) AS observations, SUM(f.impressions) AS impressions,
 SUM(f.rdv) AS rendez_vous,
 ROUND(1000.0*SUM(f.rdv)/NULLIF(SUM(f.impressions),0),2) AS rdv_par_mille,
 ROUND(SUM(f.cout_eur)/NULLIF(SUM(f.rdv),0),2) AS cout_par_rdv_eur
FROM fact_campagnes f JOIN dim_region r USING(region_id)
GROUP BY r.region ORDER BY rdv_par_mille DESC;

-- Diagnostic sectoriel pour le réseau.
SELECT r.region,s.secteur,c.campagne, SUM(f.clics) AS clics,
 SUM(f.contacts) AS contacts,SUM(f.rdv) AS rdv,
 ROUND(100.0*SUM(f.contacts)/NULLIF(SUM(f.clics),0),2) AS taux_contact_pct
FROM fact_campagnes f
JOIN dim_region r USING(region_id)
JOIN dim_secteur s USING(secteur_id)
JOIN dim_campagne c USING(campagne_id)
GROUP BY r.region,s.secteur,c.campagne
ORDER BY rdv DESC;
