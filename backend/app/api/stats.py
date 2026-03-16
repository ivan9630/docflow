"""API Stats Dashboard"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.models import Document, Supplier, AnomalyReport, DocumentStatus, DocumentType

router = APIRouter()

@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
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

@router.delete("/cleanup-logs")
async def cleanup(days: int = 30, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta
    from app.models.models import PipelineLog
    from sqlalchemy import delete
    cutoff = datetime.utcnow() - timedelta(days=days)
    r = await db.execute(delete(PipelineLog).where(PipelineLog.created_at < cutoff))
    await db.commit()
    return {"deleted": r.rowcount}
