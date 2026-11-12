-- Modèle en étoile pour une base SQLite (données fictives).
PRAGMA foreign_keys = ON;
CREATE TABLE dim_campagne (campagne_id INTEGER PRIMARY KEY, campagne TEXT NOT NULL UNIQUE);
CREATE TABLE dim_segment (segment_id INTEGER PRIMARY KEY, segment TEXT NOT NULL UNIQUE);
CREATE TABLE dim_canal (canal_id INTEGER PRIMARY KEY, canal TEXT NOT NULL UNIQUE);
CREATE TABLE dim_date (date_id INTEGER PRIMARY KEY, date TEXT NOT NULL UNIQUE);
CREATE TABLE fact_performance (
    id_ligne INTEGER PRIMARY KEY,
    campagne_id INTEGER NOT NULL REFERENCES dim_campagne(campagne_id),
    segment_id INTEGER NOT NULL REFERENCES dim_segment(segment_id),
    canal_id INTEGER NOT NULL REFERENCES dim_canal(canal_id),
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    clics INTEGER NOT NULL CHECK(clics >= 0),
    impressions INTEGER NOT NULL CHECK(impressions > 0),
    conversions INTEGER NOT NULL CHECK(conversions >= 0),
    depenses REAL NOT NULL CHECK(depenses > 0),
    revenus REAL NOT NULL CHECK(revenus >= 0)
);
