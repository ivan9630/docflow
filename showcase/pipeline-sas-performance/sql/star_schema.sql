PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS dim_region (region TEXT NOT NULL UNIQUE, region_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dim_secteur (secteur TEXT NOT NULL UNIQUE, secteur_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dim_campagne (campagne TEXT NOT NULL UNIQUE, campagne_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dim_segment (segment TEXT NOT NULL UNIQUE, segment_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dim_canal (canal TEXT NOT NULL UNIQUE, canal_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dim_semaine (semaine TEXT NOT NULL UNIQUE, semaine_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS fact_campagnes (
 record_id INTEGER PRIMARY KEY,
 impressions INTEGER NOT NULL CHECK(impressions>0),
 clics INTEGER NOT NULL CHECK(clics>=0 AND clics<=impressions),
 contacts INTEGER NOT NULL CHECK(contacts>=0 AND contacts<=clics),
 rdv INTEGER NOT NULL CHECK(rdv>=0 AND rdv<=contacts),
 cout_eur REAL NOT NULL CHECK(cout_eur>=0),
 expose INTEGER NOT NULL CHECK(expose IN (0,1)),
 post INTEGER NOT NULL CHECK(post IN (0,1)),
 region_id INTEGER NOT NULL REFERENCES dim_region(region_id),
 secteur_id INTEGER NOT NULL REFERENCES dim_secteur(secteur_id),
 campagne_id INTEGER NOT NULL REFERENCES dim_campagne(campagne_id),
 segment_id INTEGER NOT NULL REFERENCES dim_segment(segment_id),
 canal_id INTEGER NOT NULL REFERENCES dim_canal(canal_id),
 semaine_id INTEGER NOT NULL REFERENCES dim_semaine(semaine_id)
);
CREATE INDEX IF NOT EXISTS idx_fact_region_secteur ON fact_campagnes(region_id,secteur_id);
CREATE INDEX IF NOT EXISTS idx_fact_campagne_semaine ON fact_campagnes(campagne_id,semaine_id);
