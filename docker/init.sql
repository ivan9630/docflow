-- DocuFlow v2 — Initialisation PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Vue analytique enrichie
CREATE OR REPLACE VIEW v_documents_full AS
SELECT
    d.id, d.nom_fichier, d.type_document, d.statut, d.zone_actuelle,
    d.nom_fournisseur, d.numero_siren, d.numero_siret, d.numero_tva,
    d.montant_ht, d.montant_tva_val, d.montant_ttc, d.taux_tva,
    d.date_document, d.date_expiration, d.score_fraude, d.est_frauduleux,
    d.score_ocr, d.methode_ocr, d.score_classification,
    d.iban, d.numero_document,
    s.nom AS supplier_nom, s.ville AS supplier_ville,
    s.score_conformite, s.est_blackliste,
    d.created_at
FROM documents d
LEFT JOIN suppliers s ON d.supplier_id = s.id;

-- Vue conformité
CREATE OR REPLACE VIEW v_anomalies_actives AS
SELECT
    ar.id, ar.type_anomalie, ar.description, ar.severite,
    ar.champ_concerne, ar.valeur_trouvee, ar.valeur_attendue,
    ar.created_at,
    d.nom_fichier, d.type_document, d.nom_fournisseur, d.score_fraude
FROM anomaly_reports ar
JOIN documents d ON ar.document_id = d.id
WHERE ar.est_resolue = FALSE
ORDER BY
    CASE ar.severite
        WHEN 'critique' THEN 1 WHEN 'elevee' THEN 2
        WHEN 'moyenne'  THEN 3 WHEN 'faible'  THEN 4 ELSE 5
    END, ar.created_at DESC;

-- Données de démo fournisseurs
INSERT INTO suppliers (id, nom, siren, siret_siege, numero_tva, ville,
    score_conformite, attestation_urssaf_valide, attestation_fiscale_valide, created_at)
VALUES
    (uuid_generate_v4(), 'ACME Solutions SAS',   '123456789', '12345678900045',
     'FR51123456789', 'Paris',     98.5, true,  true,  NOW()),
    (uuid_generate_v4(), 'Tech Innov SARL',      '987654321', '98765432100012',
     'FR62987654321', 'Lyon',      55.0, false, false, NOW()),
    (uuid_generate_v4(), 'BuildCorp SA',         '555444333', '55544433300099',
     'FR14555444333', 'Marseille', 92.0, true,  true,  NOW()),
    (uuid_generate_v4(), 'DataFlow SAS',         '111222333', '11122233300001',
     'FR83111222333', 'Bordeaux',  78.0, true,  false, NOW()),
    (uuid_generate_v4(), 'FraudCorp SARL',       '999888777', '99988877700055',
     'FR12999888777', 'Toulouse',   0.0, false, false, NOW())
ON CONFLICT DO NOTHING;

-- Marquer FraudCorp comme blacklisté
UPDATE suppliers SET est_blackliste = true, motif_blacklist = 'Fraude documentaire avérée - SIRET falsifié'
WHERE siren = '999888777';
