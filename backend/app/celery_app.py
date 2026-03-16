"""
Pipeline Celery — DocuFlow v2
Utilise SQLAlchemy SYNC (psycopg2) car Celery n'est pas compatible asyncpg
"""
import os, time
from celery import Celery
import structlog

logger = structlog.get_logger()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery("docuflow", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json", result_serializer="json", accept_content=["json"],
    timezone="Europe/Paris", enable_utc=True,
    task_track_started=True, task_acks_late=True,
    worker_prefetch_multiplier=1, task_queues={"docuflow": {}},
    task_default_queue="docuflow",
)


@celery_app.task(bind=True, max_retries=3, name="process_document", queue="docuflow")
def process_document(self, doc_id: str, content_hex: str, filename: str, mime: str):
    """Pipeline principal — utilise SQLAlchemy synchrone (psycopg2)."""
    try:
        return _pipeline_sync(doc_id, bytes.fromhex(content_hex), filename, mime)
    except Exception as exc:
        logger.error(f"Pipeline error {doc_id}: {exc}")
        self.retry(exc=exc, countdown=30)


def _pipeline_sync(doc_id: str, content: bytes, filename: str, mime: str):
    """Pipeline 100% synchrone — compatible Celery."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import uuid as _uuid

    # Connexion SYNC (psycopg2) — pas asyncpg
    db_url = os.getenv("DATABASE_URL", "postgresql://docuflow:docuflow@postgres:5432/docuflow")
    db_url_sync = db_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url_sync, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)

    from app.models.models import (
        Document, DocumentStatus, DataZone, AnomalyReport, PipelineLog
    )
    from app.services import ocr_service, ai_service, minio_service
    import asyncio

    def run_async(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with Session() as db:
        doc = db.get(Document, _uuid.UUID(doc_id))
        if not doc:
            logger.error(f"Document {doc_id} introuvable")
            return

        steps = []

        # ── ÉTAPE 1 : RAW ────────────────────────────────────────
        t = time.time()
        doc.statut = DocumentStatus.EN_TRAITEMENT
        doc.zone_actuelle = DataZone.RAW
        try:
            raw_key = minio_service.store_raw(doc_id, filename, content)
            doc.chemin_raw = raw_key
            doc.hash_sha256 = minio_service.sha256(content)
        except Exception as e:
            logger.warning(f"MinIO RAW: {e}")
        db.commit()
        steps.append({"etape": "raw", "statut": "ok", "ms": int((time.time()-t)*1000)})
        logger.info(f"[{doc_id[:8]}] ✅ RAW stored")

        # ── ÉTAPE 2 : OCR ────────────────────────────────────────
        t = time.time()
        try:
            if mime == "application/pdf":
                ocr = ocr_service.ocr_from_pdf(content)
            else:
                ocr = ocr_service.ocr_from_image(content)
        except Exception as e:
            logger.warning(f"OCR error: {e}")
            ocr = {"text": "", "pages": [], "method": "failed", "confidence": 0.0}

        doc.texte_ocr = ocr.get("text", "")[:50000]
        doc.methode_ocr = ocr.get("method", "unknown")
        doc.score_ocr = ocr.get("confidence", 0.0)
        doc.statut = DocumentStatus.OCR_OK
        db.commit()
        steps.append({"etape": "ocr", "statut": "ok", "ms": int((time.time()-t)*1000),
                       "method": ocr.get("method"), "conf": ocr.get("confidence")})
        logger.info(f"[{doc_id[:8]}] ✅ OCR ({ocr.get('method')}, conf={ocr.get('confidence', 0):.2f})")

        # ── ÉTAPE 3 : Classification + Extraction ────────────────
        t = time.time()
        try:
            classification = run_async(ai_service.classify_document(ocr.get("text", "")))
        except Exception as e:
            logger.warning(f"Classification: {e}")
            classification = {"type_document": "autre", "confidence": 0.0, "indices": []}

        doc.type_document = classification.get("type_document", "autre")
        doc.score_classification = classification.get("confidence", 0.0)

        try:
            entities = ocr_service.extract_all(ocr.get("text", ""))
        except Exception as e:
            logger.warning(f"Extraction: {e}")
            entities = {}

        doc.numero_siren    = entities.get("siren")
        doc.numero_siret    = entities.get("siret")
        doc.numero_tva      = entities.get("tva_number")
        doc.nom_fournisseur = entities.get("company_name")
        doc.iban            = entities.get("iban")
        doc.date_document   = entities.get("date")
        doc.date_expiration = entities.get("date_expiration")
        doc.numero_document = entities.get("doc_number")
        doc.montant_ht      = entities.get("montant_ht")
        doc.montant_tva_val = entities.get("montant_tva")
        doc.montant_ttc     = entities.get("montant_ttc")
        doc.taux_tva        = entities.get("taux_tva")
        doc.donnees_extraites = entities
        doc.statut = DocumentStatus.EXTRAIT

        # Lier fournisseur
        if doc.numero_siren:
            from sqlalchemy import select
            from app.models.models import Supplier
            sup = db.query(Supplier).filter(Supplier.siren == doc.numero_siren).first()
            if sup:
                doc.supplier_id = sup.id

        db.commit()
        steps.append({"etape": "extraction", "statut": "ok", "ms": int((time.time()-t)*1000),
                       "type": str(doc.type_document)})
        logger.info(f"[{doc_id[:8]}] ✅ Extraction (type={doc.type_document})")

        # ── ÉTAPE 4 : CLEAN zone ─────────────────────────────────
        t = time.time()
        try:
            clean_key = minio_service.store_clean(doc_id, ocr, entities)
            doc.chemin_clean = clean_key
            doc.zone_actuelle = DataZone.CLEAN
        except Exception as e:
            logger.warning(f"MinIO CLEAN: {e}")
        db.commit()
        steps.append({"etape": "clean", "statut": "ok", "ms": int((time.time()-t)*1000)})

        # ── ÉTAPE 5 : Vérification fraude ────────────────────────
        t = time.time()
        local_anomalies = []

        if doc.numero_siren and doc.numero_siret:
            ok, msg = ai_service.validate_siret_siren(doc.numero_siren, doc.numero_siret)
            if not ok:
                local_anomalies.append({"type": "incoherence_siret_siren",
                    "description": msg, "severite": "critique", "champ": "siret"})

        if doc.numero_siren and doc.numero_tva:
            ok, msg = ai_service.validate_tva_local(doc.numero_siren, doc.numero_tva)
            if not ok:
                local_anomalies.append({"type": "incoherence_tva",
                    "description": msg, "severite": "elevee", "champ": "tva"})

        if doc.montant_ht and doc.montant_ttc:
            ok, msg = ai_service.validate_amounts(
                doc.montant_ht, doc.montant_tva_val, doc.montant_ttc, doc.taux_tva)
            if not ok:
                local_anomalies.append({"type": "montant_incoherent",
                    "description": msg, "severite": "elevee", "champ": "montants"})

        # Vérification IA Claude
        try:
            fraud = run_async(ai_service.detect_anomalies(
                str(doc.type_document), entities, {}, []))
        except Exception as e:
            logger.warning(f"Fraud detection: {e}")
            fraud = {"score_fraude": 0.0, "est_frauduleux": False, "anomalies": []}

        all_anomalies = local_anomalies + fraud.get("anomalies", [])
        doc.score_fraude   = max(fraud.get("score_fraude", 0.0), len(local_anomalies) * 0.2)
        doc.est_frauduleux = fraud.get("est_frauduleux", False) or doc.score_fraude > 0.7
        doc.anomalies      = all_anomalies

        for a in all_anomalies:
            db.add(AnomalyReport(
                id=_uuid.uuid4(), document_id=doc.id,
                type_anomalie=a.get("type", ""),
                description=a.get("description", ""),
                severite=a.get("severite", "faible"),
                champ_concerne=a.get("champ", ""),
                valeur_trouvee=str(a.get("valeur_trouvee", "")),
                valeur_attendue=str(a.get("valeur_attendue", "")),
            ))

        doc.statut = DocumentStatus.ANOMALIE if all_anomalies else DocumentStatus.VERIFIE
        db.commit()
        steps.append({"etape": "verification", "statut": "ok",
                       "ms": int((time.time()-t)*1000),
                       "score_fraude": doc.score_fraude,
                       "anomalies": len(all_anomalies)})
        logger.info(f"[{doc_id[:8]}] ✅ Vérification (fraude={doc.score_fraude:.2f})")

        # ── ÉTAPE 6 : CURATED + Enrichissement ──────────────────
        t = time.time()
        try:
            enriched = run_async(ai_service.enrich_for_crm(str(doc.type_document), entities, fraud))
        except Exception as e:
            logger.warning(f"Enrichment: {e}")
            enriched = entities

        curated = {
            "doc_id": doc_id, "type": str(doc.type_document),
            "entities": entities, "fraud": fraud,
            "enriched": enriched, "pipeline_steps": steps,
        }
        try:
            gold_key = minio_service.store_curated(doc_id, curated)
            doc.chemin_curated   = gold_key
            doc.donnees_enrichies = enriched
            doc.zone_actuelle    = DataZone.CURATED
        except Exception as e:
            logger.warning(f"MinIO CURATED: {e}")

        doc.pipeline_steps = steps
        doc.statut = DocumentStatus.ANOMALIE if all_anomalies else DocumentStatus.VALIDE
        db.commit()

        steps.append({"etape": "curated", "statut": "ok", "ms": int((time.time()-t)*1000)})
        logger.info(f"[{doc_id[:8]}] 🏁 Pipeline terminé — statut={doc.statut}")

        engine.dispose()
        return {
            "doc_id": doc_id, "statut": str(doc.statut),
            "type": str(doc.type_document),
            "score_fraude": doc.score_fraude,
            "anomalies": len(all_anomalies),
        }
