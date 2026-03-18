"""API Conformité"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.db.database import get_db
from app.models.models import Document, AnomalyReport, DocumentStatus, Supplier, User
from app.services.auth_service import require_role
import uuid
router = APIRouter()


@router.get("/anomalies")
async def anomalies(resolved: bool = False, severite: str = None, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("conformite", "admin"))):
    q = select(AnomalyReport).where(AnomalyReport.est_resolue == resolved).order_by(desc(AnomalyReport.created_at)).limit(200)
    if severite: q = q.where(AnomalyReport.severite == severite)
    r = await db.execute(q)
    return [{"id":str(a.id),"document_id":str(a.document_id),"type":a.type_anomalie,
             "description":a.description,"severite":a.severite,"champ":a.champ_concerne,
             "valeur_trouvee":a.valeur_trouvee,"valeur_attendue":a.valeur_attendue,
             "created_at":a.created_at.isoformat() if a.created_at else None} for a in r.scalars().all()]


@router.get("/fraudulent")
async def fraudulent(db: AsyncSession = Depends(get_db), user: User = Depends(require_role("conformite", "admin"))):
    r = await db.execute(select(Document).where(Document.est_frauduleux==True).order_by(desc(Document.score_fraude)))
    return [{"id":str(d.id),"nom":d.nom_fichier,"type":str(d.type_document),
             "fournisseur":d.nom_fournisseur,"score":d.score_fraude,"anomalies":d.anomalies} for d in r.scalars().all()]


@router.patch("/anomalies/{aid}/resolve")
async def resolve(aid: str, resolution: str = "Résolu manuellement", db: AsyncSession = Depends(get_db), user: User = Depends(require_role("conformite", "admin"))):
    a = await db.get(AnomalyReport, uuid.UUID(aid))
    if not a: raise HTTPException(404)
    a.est_resolue = True; a.resolution = resolution
    await db.commit()
    return {"message": "Anomalie résolue"}


@router.get("/check-inter-docs", summary="Vérification cohérence inter-documents")
async def check_inter_docs(db: AsyncSession = Depends(get_db)):
    """Compare les données entre documents du même fournisseur."""
    from sqlalchemy import and_
    new_anomalies = 0
    # Récupérer tous les fournisseurs avec plusieurs documents
    r = await db.execute(select(Supplier))
    suppliers = r.scalars().all()
    for sup in suppliers:
        r2 = await db.execute(select(Document).where(Document.supplier_id == sup.id))
        docs = r2.scalars().all()
        sirets = list({d.numero_siret for d in docs if d.numero_siret})
        ibans  = list({d.iban for d in docs if d.iban})
        # Incohérence SIRET entre docs
        if len(sirets) > 1:
            for doc in docs:
                if doc.numero_siret and doc.numero_siret not in sirets[:1]:
                    db.add(AnomalyReport(
                        id=uuid.uuid4(), document_id=doc.id,
                        type_anomalie="incoherence_siret_inter_docs",
                        description=f"SIRET {doc.numero_siret} différent du SIRET référence {sirets[0]}",
                        severite="critique", champ_concerne="siret",
                        valeur_trouvee=doc.numero_siret, valeur_attendue=sirets[0]
                    ))
                    new_anomalies += 1
        # Incohérence IBAN entre docs
        if len(ibans) > 1:
            for doc in docs:
                if doc.iban and doc.iban not in ibans[:1]:
                    db.add(AnomalyReport(
                        id=uuid.uuid4(), document_id=doc.id,
                        type_anomalie="incoherence_iban_inter_docs",
                        description=f"IBAN différent du référentiel fournisseur",
                        severite="elevee", champ_concerne="iban",
                        valeur_trouvee=doc.iban[:12]+"...", valeur_attendue=ibans[0][:12]+"..."
                    ))
                    new_anomalies += 1
    await db.commit()
    return {"new_anomalies": new_anomalies}


@router.post("/refresh")
async def refresh_compliance(db: AsyncSession = Depends(get_db), user: User = Depends(require_role("conformite", "admin"))):
    """Recalcule les scores de conformité fournisseurs."""
    r = await db.execute(select(Supplier))
    suppliers = r.scalars().all()
    for sup in suppliers:
        score = 100.0
        if not sup.attestation_urssaf_valide:  score -= 20
        if not sup.attestation_fiscale_valide: score -= 15
        if not sup.iban:                       score -= 10
        if sup.est_blackliste:                 score = 0
        sup.score_conformite = max(0.0, score)
    await db.commit()
    return {"message": f"{len(suppliers)} fournisseurs mis à jour"}
