"""Modèles SQLAlchemy — DocuFlow v2"""
from sqlalchemy import (
    Column, String, Float, DateTime, Boolean, Text, JSON,
    Integer, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
import uuid, enum
from datetime import datetime


class Base(DeclarativeBase):
    pass


class DocumentType(str, enum.Enum):
    FACTURE             = "facture"
    DEVIS               = "devis"
    BON_COMMANDE        = "bon_commande"
    ATTESTATION_URSSAF  = "attestation_urssaf"
    ATTESTATION_FISCALE = "attestation_fiscale"
    KBIS                = "kbis"
    RIB                 = "rib"
    CONTRAT             = "contrat"
    AUTRE               = "autre"


class DocumentStatus(str, enum.Enum):
    UPLOADE       = "uploade"
    EN_TRAITEMENT = "en_traitement"
    OCR_OK        = "ocr_ok"
    EXTRAIT       = "extrait"
    VERIFIE       = "verifie"
    ANOMALIE      = "anomalie"
    VALIDE        = "valide"
    REJETE        = "rejete"


class DataZone(str, enum.Enum):
    RAW     = "raw"      # Fichier brut
    CLEAN   = "clean"    # Texte OCR + JSON
    CURATED = "curated"  # Enrichi, prêt métier


class Document(Base):
    __tablename__ = "documents"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom_fichier          = Column(String(500), nullable=False)
    mime_type            = Column(String(100))
    taille_fichier       = Column(Integer)
    hash_sha256          = Column(String(64))
    type_document        = Column(SAEnum(DocumentType))
    statut               = Column(SAEnum(DocumentStatus), default=DocumentStatus.UPLOADE)
    zone_actuelle        = Column(SAEnum(DataZone), default=DataZone.RAW)

    # Chemins MinIO
    chemin_raw           = Column(String(1000))
    chemin_clean         = Column(String(1000))
    chemin_curated       = Column(String(1000))

    # OCR
    texte_ocr            = Column(Text)
    methode_ocr          = Column(String(50))
    score_ocr            = Column(Float)
    score_classification = Column(Float)

    # Entités extraites
    numero_siren         = Column(String(20))
    numero_siret         = Column(String(20))
    numero_tva           = Column(String(30))
    nom_fournisseur      = Column(String(500))
    montant_ht           = Column(Float)
    montant_tva_val      = Column(Float)
    taux_tva             = Column(Float)
    montant_ttc          = Column(Float)
    date_document        = Column(String(50))
    date_echeance        = Column(String(50))
    date_expiration      = Column(String(50))  # Pour attestations
    numero_document      = Column(String(200))
    iban                 = Column(String(50))
    bic                  = Column(String(20))
    adresse_fournisseur  = Column(Text)

    # Données structurées complètes
    donnees_extraites    = Column(JSON, default=dict)
    donnees_enrichies    = Column(JSON, default=dict)

    # Scores et fraude
    score_fraude         = Column(Float, default=0.0)
    est_frauduleux       = Column(Boolean, default=False)
    anomalies            = Column(JSON, default=list)

    # Airflow
    airflow_run_id       = Column(String(200))
    pipeline_steps       = Column(JSON, default=list)

    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier_id          = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    supplier             = relationship("Supplier", back_populates="documents")
    anomaly_reports      = relationship("AnomalyReport", back_populates="document", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id                          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom                         = Column(String(500), nullable=False)
    siren                       = Column(String(20), unique=True)
    siret_siege                 = Column(String(20))
    numero_tva                  = Column(String(30))
    iban                        = Column(String(50))
    bic                         = Column(String(20))
    adresse                     = Column(Text)
    code_postal                 = Column(String(10))
    ville                       = Column(String(200))
    pays                        = Column(String(100), default="France")
    email                       = Column(String(300))
    telephone                   = Column(String(30))
    code_naf                    = Column(String(10))
    forme_juridique             = Column(String(100))

    # Conformité
    score_conformite            = Column(Float, default=100.0)
    est_blackliste              = Column(Boolean, default=False)
    motif_blacklist             = Column(Text)
    attestation_urssaf_valide   = Column(Boolean, default=False)
    attestation_urssaf_date_exp = Column(String(50))
    attestation_fiscale_valide  = Column(Boolean, default=False)
    kbis_date                   = Column(String(50))

    # Données SIRENE
    date_creation_entreprise    = Column(String(50))
    effectif                    = Column(String(50))
    chiffre_affaires            = Column(Float)

    created_at                  = Column(DateTime, default=datetime.utcnow)
    updated_at                  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents                   = relationship("Document", back_populates="supplier")


class AnomalyReport(Base):
    __tablename__ = "anomaly_reports"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id    = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    type_anomalie  = Column(String(200))
    description    = Column(Text)
    severite       = Column(String(20))
    champ_concerne = Column(String(100))
    valeur_trouvee = Column(String(500))
    valeur_attendue= Column(String(500))
    est_resolue    = Column(Boolean, default=False)
    resolution     = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)

    document       = relationship("Document", back_populates="anomaly_reports")


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id    = Column(UUID(as_uuid=True))
    etape          = Column(String(100))
    statut         = Column(String(50))
    message        = Column(Text)
    duree_ms       = Column(Integer)
    created_at     = Column(DateTime, default=datetime.utcnow)
