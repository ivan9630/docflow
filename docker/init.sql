-- DocuFlow v2 — Initialisation PostgreSQL
-- Les tables sont créées par SQLAlchemy (FastAPI lifespan)
-- Ce script ne contient que les extensions et données de démo

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Les vues seront créées APRÈS le démarrage du backend
-- car elles dépendent des tables gérées par SQLAlchemy
