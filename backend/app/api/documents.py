"""API Documents"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import uuid, magic
import structlog

from app.db.database import get_db
from app.models.models import Document, DocumentStatus, DataZone
from app.services.minio_service import store_raw, sha256
from app.celery_app import process_document

logger = structlog.get_logger()
router = APIRouter()

ALLOWED = {"application/pdf","image/jpeg","image/png","image/tiff","image/webp"}
MAX_SIZE = 50 * 1024 * 1024


@router.post("/upload", summary="Upload multi-documents (max 20 fichiers)")
async def upload(files: List[UploadFile] = File(...), db: AsyncSession = Depends(get_db)):
    if len(files) > 20:
        raise HTTPException(400, "Maximum 20 fichiers par upload")
    results = []
    for f in files:
        content = await f.read()
        if len(content) > MAX_SIZE:
            results.append({"filename": f.filename, "status": "error", "message": "Fichier > 50MB"}); continue
        mime = magic.from_buffer(content, mime=True)
        if mime not in ALLOWED:
            results.append({"filename": f.filename, "status": "error", "message": f"Type non supporté: {mime}"}); continue
        doc_id = uuid.uuid4()
        doc = Document(id=doc_id, nom_fichier=f.filename, mime_type=mime,
                       taille_fichier=len(content), hash_sha256=sha256(content),
                       statut=DocumentStatus.UPLOADE, zone_actuelle=DataZone.RAW)
        db.add(doc)
        await db.flush()
        try:
            key = store_raw(str(doc_id), f.filename, content)
            doc.chemin_raw = key
        except Exception as e:
            logger.warning(f"Raw store: {e}")
        await db.commit()
        process_document.delay(str(doc_id), content.hex(), f.filename, mime)
        results.append({"doc_id": str(doc_id), "filename": f.filename, "status": "queued", "mime": mime})
        logger.info(f"📤 Upload: {f.filename} → {doc_id}")
    return {"uploaded": sum(1 for r in results if r["status"]=="queued"), "results": results}


@router.post("/{doc_id}/process", summary="Relancer le pipeline pour un document")
async def reprocess(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc: raise HTTPException(404, "Document introuvable")
    if not doc.chemin_raw: raise HTTPException(400, "Fichier RAW introuvable")
    from app.services.minio_service import get_raw
    content = get_raw(doc.chemin_raw)
    process_document.delay(doc_id, content.hex(), doc.nom_fichier, doc.mime_type or "application/pdf")
    return {"message": "Pipeline relancé", "doc_id": doc_id}


@router.get("/", summary="Liste des documents")
async def list_docs(
    status: Optional[str] = None, doc_type: Optional[str] = None,
    limit: int = Query(50, le=500), offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    q = select(Document).order_by(desc(Document.created_at)).limit(limit).offset(offset)
    if status:   q = q.where(Document.statut == status)
    if doc_type: q = q.where(Document.type_document == doc_type)
    r = await db.execute(q)
    docs = r.scalars().all()
    return {"total": len(docs), "documents": [_ser(d) for d in docs]}


@router.get("/{doc_id}", summary="Détail complet d'un document")
async def get_doc(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc: raise HTTPException(404, "Document introuvable")
    return _ser(doc, full=True)


@router.get("/{doc_id}/status")
async def doc_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc: raise HTTPException(404)
    return {
        "doc_id": doc_id,
        "statut": doc.statut.value if doc.statut else None,
        "zone": doc.zone_actuelle.value if doc.zone_actuelle else None,
        "type": doc.type_document.value if doc.type_document else None,
        "score_fraude": doc.score_fraude,
        "anomalies": len(doc.anomalies or []),
        "pipeline_steps": doc.pipeline_steps,
    }


@router.patch("/{doc_id}/validate")
async def validate(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc: raise HTTPException(404)
    doc.statut = DocumentStatus.VALIDE
    await db.commit()
    return {"message": "Validé"}


@router.patch("/{doc_id}/reject")
async def reject(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc: raise HTTPException(404)
    doc.statut = DocumentStatus.REJETE
    await db.commit()
    return {"message": "Rejeté"}


def _ser(d: Document, full=False) -> dict:
    """Sérialise un document — utilise .value pour les enums."""
    base = {
        "id": str(d.id),
        "nom_fichier": d.nom_fichier,
        "type_document": d.type_document.value if d.type_document else None,
        "statut": d.statut.value if d.statut else None,
        "zone": d.zone_actuelle.value if d.zone_actuelle else None,
        "nom_fournisseur": d.nom_fournisseur,
        "numero_siren": d.numero_siren,
        "montant_ttc": d.montant_ttc,
        "date_document": d.date_document,
        "score_fraude": d.score_fraude,
        "est_frauduleux": d.est_frauduleux,
        "anomalies_count": len(d.anomalies or []),
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
    if full:
        base.update({
            "numero_siret": d.numero_siret,
            "numero_tva": d.numero_tva,
            "montant_ht": d.montant_ht,
            "montant_tva_val": d.montant_tva_val,
            "taux_tva": d.taux_tva,
            "iban": d.iban,
            "bic": d.bic,
            "numero_document": d.numero_document,
            "date_expiration": d.date_expiration,
            "score_ocr": d.score_ocr,
            "methode_ocr": d.methode_ocr,
            "score_classification": d.score_classification,
            "anomalies": d.anomalies,
            "donnees_extraites": d.donnees_extraites,
            "donnees_enrichies": d.donnees_enrichies,
            "chemin_raw": d.chemin_raw,
            "chemin_clean": d.chemin_clean,
            "chemin_curated": d.chemin_curated,
            "hash_sha256": d.hash_sha256,
            "pipeline_steps": d.pipeline_steps,
            "airflow_run_id": d.airflow_run_id,
        })
    return base
