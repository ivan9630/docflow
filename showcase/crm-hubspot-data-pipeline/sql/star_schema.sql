PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS dim_source (source_id INTEGER PRIMARY KEY, source TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS dim_secteur (secteur_id INTEGER PRIMARY KEY, secteur TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS dim_region (region_id INTEGER PRIMARY KEY, region TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS dim_statut (statut_id INTEGER PRIMARY KEY, statut TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS fact_leads (
 lead_id TEXT PRIMARY KEY, nom TEXT NOT NULL, email TEXT UNIQUE NOT NULL, entreprise TEXT NOT NULL,
 source_id INTEGER REFERENCES dim_source(source_id), secteur_id INTEGER REFERENCES dim_secteur(secteur_id),
 region_id INTEGER REFERENCES dim_region(region_id), statut_id INTEGER REFERENCES dim_statut(statut_id),
 derniere_interaction TEXT NOT NULL, nb_interactions INTEGER CHECK(nb_interactions>=0),
 pages_visitees INTEGER CHECK(pages_visitees>=0), taille_entreprise INTEGER CHECK(taille_entreprise>=0),
 budget_indicatif REAL CHECK(budget_indicatif>=0), contacts_livres INTEGER CHECK(contacts_livres>=0),
 contacts_convertis INTEGER CHECK(contacts_convertis>=0 AND contacts_convertis<=contacts_livres),
 litiges INTEGER CHECK(litiges IN (0,1)), cout_acquisition REAL CHECK(cout_acquisition>=0),
 ca_facture REAL CHECK(ca_facture>=0), montant_facture REAL CHECK(montant_facture>=0),
 score_qualite REAL, score_conversion_ml REAL, segment TEXT, ecart_facturation REAL
);
CREATE INDEX IF NOT EXISTS idx_lead_seg ON fact_leads(segment);
CREATE INDEX IF NOT EXISTS idx_lead_src ON fact_leads(source_id);
