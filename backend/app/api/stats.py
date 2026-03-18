"""API Stats Dashboard"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.models import Document, Supplier, AnomalyReport, PipelineLog, DocumentStatus, DocumentType, User
from app.services.auth_service import get_current_user, require_role

router = APIRouter()


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    total_docs = await db.scalar(select(func.count(Document.id))) or 0
    fraud      = await db.scalar(select(func.count(Document.id)).where(Document.est_frauduleux==True)) or 0
    open_anom  = await db.scalar(select(func.count(AnomalyReport.id)).where(AnomalyReport.est_resolue==False)) or 0
    total_sup  = await db.scalar(select(func.count(Supplier.id))) or 0
    blacklisted= await db.scalar(select(func.count(Supplier.id)).where(Supplier.est_blackliste==True)) or 0
    total_amt  = await db.scalar(select(func.sum(Document.montant_ttc)).where(Document.type_document==DocumentType.FACTURE)) or 0

    by_status  = dict((await db.execute(select(Document.statut,func.count(Document.id)).group_by(Document.statut))).all())
    by_type    = dict((await db.execute(select(Document.type_document,func.count(Document.id)).where(Document.type_document!=None).group_by(Document.type_document))).all())
    by_zone    = dict((await db.execute(select(Document.zone_actuelle,func.count(Document.id)).group_by(Document.zone_actuelle))).all())

    return {
        "documents": {"total":total_docs,"fraudulent":fraud,"by_status":{str(k):v for k,v in by_status.items()},"by_type":{str(k):v for k,v in by_type.items()},"by_zone":{str(k):v for k,v in by_zone.items()}},
        "anomalies": {"open":open_anom},
        "suppliers": {"total":total_sup,"blacklisted":blacklisted},
        "financials": {"total_invoiced":round(float(total_amt),2)},
    }


@router.get("/admin")
async def admin_stats(db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    """Stats detaillees pour le dashboard admin."""
    total_docs = await db.scalar(select(func.count(Document.id))) or 0
    fraud = await db.scalar(select(func.count(Document.id)).where(Document.est_frauduleux==True)) or 0
    open_anom = await db.scalar(select(func.count(AnomalyReport.id)).where(AnomalyReport.est_resolue==False)) or 0
    resolved_anom = await db.scalar(select(func.count(AnomalyReport.id)).where(AnomalyReport.est_resolue==True)) or 0
    total_sup = await db.scalar(select(func.count(Supplier.id))) or 0
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_amt = await db.scalar(select(func.sum(Document.montant_ttc)).where(Document.type_document==DocumentType.FACTURE)) or 0

    # Repartition par type
    by_type = dict((await db.execute(select(Document.type_document, func.count(Document.id)).where(Document.type_document!=None).group_by(Document.type_document))).all())
    # Repartition par zone
    by_zone = dict((await db.execute(select(Document.zone_actuelle, func.count(Document.id)).group_by(Document.zone_actuelle))).all())
    # Repartition par statut
    by_status = dict((await db.execute(select(Document.statut, func.count(Document.id)).group_by(Document.statut))).all())

    # Anomalies par severite
    anom_by_sev = dict((await db.execute(select(AnomalyReport.severite, func.count(AnomalyReport.id)).group_by(AnomalyReport.severite))).all())
    # Anomalies par type
    anom_by_type = dict((await db.execute(select(AnomalyReport.type_anomalie, func.count(AnomalyReport.id)).group_by(AnomalyReport.type_anomalie))).all())

    # Metriques OCR
    avg_ocr = await db.scalar(select(func.avg(Document.score_ocr)).where(Document.score_ocr!=None)) or 0
    avg_classif = await db.scalar(select(func.avg(Document.score_classification)).where(Document.score_classification!=None)) or 0

    # Metriques pipeline (temps moyen par etape)
    pipeline_perf = dict((await db.execute(
        select(PipelineLog.etape, func.avg(PipelineLog.duree_ms))
        .where(PipelineLog.duree_ms!=None)
        .group_by(PipelineLog.etape)
    )).all())

    # Conformite fournisseurs
    avg_conformite = await db.scalar(select(func.avg(Supplier.score_conformite))) or 0
    blacklisted = await db.scalar(select(func.count(Supplier.id)).where(Supplier.est_blackliste==True)) or 0

    return {
        "overview": {
            "total_documents": total_docs,
            "total_suppliers": total_sup,
            "total_users": total_users,
            "total_invoiced": round(float(total_amt), 2),
        },
        "documents": {
            "by_type": {str(k).replace("DocumentType.", ""): v for k, v in by_type.items()},
            "by_zone": {str(k).replace("DataZone.", ""): v for k, v in by_zone.items()},
            "by_status": {str(k).replace("DocumentStatus.", ""): v for k, v in by_status.items()},
        },
        "fraud": {
            "fraudulent_docs": fraud,
            "fraud_rate": round(fraud / total_docs * 100, 1) if total_docs > 0 else 0,
        },
        "anomalies": {
            "open": open_anom,
            "resolved": resolved_anom,
            "by_severity": anom_by_sev,
            "by_type": anom_by_type,
        },
        "ai_quality": {
            "avg_ocr_confidence": round(float(avg_ocr) * 100, 1),
            "avg_classification_confidence": round(float(avg_classif) * 100, 1),
            "classifier_model": "TF-IDF + LinearSVC",
            "classifier_accuracy": 99.73,
            "classifier_f1": 99.73,
            "classes": 11,
            "training_samples": 5500,
        },
        "pipeline": {
            "avg_time_ms": {str(k): round(float(v)) for k, v in pipeline_perf.items()},
        },
        "suppliers": {
            "total": total_sup,
            "blacklisted": blacklisted,
            "avg_conformity": round(float(avg_conformite), 1),
        },
    }


@router.delete("/cleanup-logs")
async def cleanup(days: int = 30, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    cutoff = datetime.utcnow() - timedelta(days=days)
    r = await db.execute(delete(PipelineLog).where(PipelineLog.created_at < cutoff))
    await db.commit()
    return {"deleted": r.rowcount}
