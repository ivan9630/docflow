"""
Pipeline Celery — DocuFlow v2
6 étapes : RAW → OCR → NER → Validation → CLEAN → CURATED
"""
import os, asyncio, time
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


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: return loop.run_until_complete(coro)
    finally: loop.close()


def _log_step(db_session, doc_id, step, status, msg, duration_ms=0):
    from app.models.models import PipelineLog
    import uuid
    log = PipelineLog(
        id=uuid.uuid4(), document_id=doc_id,
        etape=step, statut=status, message=msg, duree_ms=duration_ms
    )
    db_session.add(log)


@celery_app.task(bind=True, max_retries=3, name="process_document", queue="docuflow")
def process_document(self, doc_id: str, content_hex: str, filename: str, mime: str):
    """Pipeline principal : 6 étapes orchestrées."""
    try:
        return _run(_pipeline(doc_id, bytes.fromhex(content_hex), filename, mime))
    except Exception as exc:
        logger.error(f"Pipeline error {doc_id}: {exc}")
        self.retry(exc=exc, countdown=30)


async def _pipeline(doc_id: str, content: bytes, filename: str, mime: str):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    import os
    from app.models.models import Document, DocumentStatus, DataZone, AnomalyReport
    from app.services import ocr_service, ai_service, minio_service
    import uuid as _uuid

    # Créer un engine frais par task pour éviter les conflits asyncpg
    _url = os.getenv("DATABASE_URL", "postgresql+asyncpg://docuflow:docuflow@localhost:5432/docuflow")
    _engine = create_async_engine(_url, echo=False, pool_size=1, max_overflow=0)
    _Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _Session() as db:
        doc = await db.get(Document, _uuid.UUID(doc_id))
        if not doc: return

        steps = []

        # ── ÉTAPE 1 : RAW ────────────────────────────────────────
        t = time.time()
        doc.statut = DocumentStatus.EN_TRAITEMENT
        doc.zone_actuelle = DataZone.RAW
        raw_key = minio_service.store_raw(doc_id, filename, content)
        doc.chemin_raw = raw_key
        doc.hash_sha256 = minio_service.sha256(content)
        duration = int((time.time()-t)*1000)
        steps.append({"etape":"raw","statut":"ok","ms":duration})
        logger.info(f"[{doc_id[:8]}] ✅ RAW stored")

        # ── ÉTAPE 2 : OCR ────────────────────────────────────────
        t = time.time()
        if mime == "application/pdf":
            ocr = ocr_service.ocr_from_pdf(content)
        else:
            ocr = ocr_service.ocr_from_image(content)
        doc.texte_ocr = ocr["text"][:50000]
        doc.methode_ocr = ocr["method"]
        doc.score_ocr = ocr["confidence"]
        doc.statut = DocumentStatus.OCR_OK
        duration = int((time.time()-t)*1000)
        steps.append({"etape":"ocr","statut":"ok","ms":duration,"method":ocr["method"],"conf":ocr["confidence"]})
        logger.info(f"[{doc_id[:8]}] ✅ OCR done ({ocr['method']}, conf={ocr['confidence']:.2f})")

        # ── ÉTAPE 3 : Classification + Extraction entités ────────
        t = time.time()
        from app.services import classifier_service
        local_clf = classifier_service.classify_local(ocr["text"])
        if local_clf and local_clf["confidence"] > 0.3:
            classification = local_clf
            logger.info(f"[{doc_id[:8]}] Classification locale : {local_clf['type_document']} (conf={local_clf['confidence']:.2f})")
        else:
            classification = await ai_service.classify_document(ocr["text"])
            logger.info(f"[{doc_id[:8]}] Classification Claude fallback : {classification.get('type_document')}")
        doc.type_document = classification.get("type_document", "autre")
        doc.score_classification = classification.get("confidence", 0.0)

        entities = ocr_service.extract_all(ocr["text"])
        doc.numero_siren      = entities.get("siren")
        doc.numero_siret      = entities.get("siret")
        doc.numero_tva        = entities.get("tva_number")
        doc.nom_fournisseur   = entities.get("company_name")
        doc.iban              = entities.get("iban")
        doc.date_document     = entities.get("date")
        doc.date_expiration   = entities.get("date_expiration")
        doc.numero_document   = entities.get("doc_number")
        doc.montant_ht        = entities.get("montant_ht")
        doc.montant_tva_val   = entities.get("montant_tva")
        doc.montant_ttc       = entities.get("montant_ttc")
        doc.taux_tva          = entities.get("taux_tva")
        doc.adresse_fournisseur = entities.get("adresse")
        doc.donnees_extraites = entities
        doc.statut = DocumentStatus.EXTRAIT

        # Lier ou créer fournisseur
        if doc.numero_siren:
            from sqlalchemy import select
            from app.models.models import Supplier
            res = await db.execute(select(Supplier).where(Supplier.siren == doc.numero_siren))
            sup = res.scalar_one_or_none()
            if not sup:
                sup = Supplier(
                    id=_uuid.uuid4(),
                    siren=doc.numero_siren,
                    siret_siege=doc.numero_siret,
                    nom=doc.nom_fournisseur or f"Fournisseur {doc.numero_siren}",
                    numero_tva=doc.numero_tva,
                    iban=doc.iban,
                    adresse=entities.get("adresse"),
                    code_postal=entities.get("code_postal"),
                    ville=entities.get("ville"),
                    score_conformite=100.0,
                )
                db.add(sup)
                await db.flush()
                logger.info(f"[{doc_id[:8]}] Fournisseur créé : {sup.nom} (SIREN {sup.siren})")
            doc.supplier_id = sup.id

        duration = int((time.time()-t)*1000)
        steps.append({"etape":"extraction","statut":"ok","ms":duration,"type":str(doc.type_document)})
        logger.info(f"[{doc_id[:8]}] ✅ Extraction done (type={doc.type_document})")

        # ── ÉTAPE 4 : CLEAN zone ─────────────────────────────────
        t = time.time()
        clean_key = minio_service.store_clean(doc_id, ocr, entities)
        doc.chemin_clean = clean_key
        doc.zone_actuelle = DataZone.CLEAN
        duration = int((time.time()-t)*1000)
        steps.append({"etape":"clean","statut":"ok","ms":duration})

        # ── ÉTAPE 5 : Vérification fraude + anomalies ────────────
        t = time.time()
        supplier_data = {}
        if doc.supplier_id:
            from app.models.models import Supplier
            sup = await db.get(Supplier, doc.supplier_id)
            if sup:
                supplier_data = {"siren":sup.siren,"siret":sup.siret_siege,"tva":sup.numero_tva,"iban":sup.iban}

        # Vérification locale (sans API) — modèle local en premier
        fraud = ai_service.detect_anomalies_local(
            str(doc.type_document), entities, supplier_data
        )

        all_anomalies = fraud.get("anomalies", [])

        # Document de type "autre" → anomalie automatique
        if str(doc.type_document) in ("autre", "DocumentType.AUTRE"):
            all_anomalies.append({
                "type": "type_non_reconnu",
                "description": "Type de document non reconnu par le classifieur. Vérification manuelle requise.",
                "severite": "elevee",
                "champ": "type_document",
                "valeur_trouvee": "autre",
                "valeur_attendue": "facture, devis, attestation, kbis, rib, contrat..."
            })
            fraud["score_fraude"] = max(fraud.get("score_fraude", 0.0), 0.4)

        logger.info(f"[{doc_id[:8]}] Vérification locale : {len(all_anomalies)} anomalie(s), score={fraud['score_fraude']}")

        doc.score_fraude = fraud.get("score_fraude", 0.0)
        doc.est_frauduleux = fraud.get("est_frauduleux", False)
        doc.anomalies = all_anomalies

        # Sauvegarder rapports d'anomalies
        for a in all_anomalies:
            from app.models.models import AnomalyReport
            import uuid
            db.add(AnomalyReport(
                id=uuid.uuid4(), document_id=doc.id,
                type_anomalie=a.get("type",""), description=a.get("description",""),
                severite=a.get("severite","faible"), champ_concerne=a.get("champ",""),
                valeur_trouvee=str(a.get("valeur_trouvee","")),
                valeur_attendue=str(a.get("valeur_attendue",""))
            ))

        doc.statut = DocumentStatus.ANOMALIE if all_anomalies else DocumentStatus.VERIFIE
        duration = int((time.time()-t)*1000)
        steps.append({"etape":"verification","statut":"ok","ms":duration,
                       "score_fraude":doc.score_fraude,"anomalies":len(all_anomalies)})
        logger.info(f"[{doc_id[:8]}] ✅ Vérification done (score_fraude={doc.score_fraude:.2f})")

        # ── ÉTAPE 6 : CURATED + Enrichissement ──────────────────
        t = time.time()
        enriched = ai_service.enrich_local(str(doc.type_document), entities, fraud)
        curated_payload = {
            "doc_id": doc_id, "type": str(doc.type_document),
            "entities": entities, "fraud": fraud,
            "enriched": enriched, "ocr_method": ocr["method"],
            "pipeline_steps": steps,
        }
        curated_key = minio_service.store_curated(doc_id, curated_payload)
        doc.chemin_curated = curated_key
        doc.donnees_enrichies = enriched
        doc.zone_actuelle = DataZone.CURATED
        doc.pipeline_steps = steps
        duration = int((time.time()-t)*1000)
        steps.append({"etape":"curated","statut":"ok","ms":duration})

        # Statut final
        if doc.est_frauduleux: doc.statut = DocumentStatus.ANOMALIE
        elif all_anomalies:    doc.statut = DocumentStatus.ANOMALIE
        else:                  doc.statut = DocumentStatus.VALIDE

        await db.commit()
        logger.info(f"[{doc_id[:8]}] Pipeline termine — statut={doc.statut}")

        result = {"doc_id":doc_id,"statut":str(doc.statut),"type":str(doc.type_document),
                "score_fraude":doc.score_fraude,"anomalies":len(all_anomalies)}

    await _engine.dispose()
    return result
