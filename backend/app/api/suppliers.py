"""API Fournisseurs"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import uuid
from app.db.database import get_db
from app.models.models import Supplier, Document

router = APIRouter()


class SupplierIn(BaseModel):
    nom: str
    siren: Optional[str]=None; siret_siege: Optional[str]=None
    numero_tva: Optional[str]=None; iban: Optional[str]=None; bic: Optional[str]=None
    adresse: Optional[str]=None; code_postal: Optional[str]=None; ville: Optional[str]=None
    email: Optional[str]=None; telephone: Optional[str]=None
    forme_juridique: Optional[str]=None; code_naf: Optional[str]=None


@router.get("/")
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Supplier).order_by(Supplier.nom))
    return [_ser(s) for s in r.scalars().all()]


@router.post("/")
async def create_supplier(data: SupplierIn, db: AsyncSession = Depends(get_db)):
    s = Supplier(**data.model_dump())
    db.add(s); await db.commit(); await db.refresh(s)
    return _ser(s, full=True)


@router.get("/{sid}")
async def get_supplier(sid: str, db: AsyncSession = Depends(get_db)):
    s = await db.get(Supplier, uuid.UUID(sid))
    if not s: raise HTTPException(404)
    return _ser(s, full=True)


@router.patch("/{sid}")
async def update_supplier(sid: str, data: dict, db: AsyncSession = Depends(get_db)):
    s = await db.get(Supplier, uuid.UUID(sid))
    if not s: raise HTTPException(404)
    for k,v in data.items():
        if hasattr(s, k): setattr(s, k, v)
    await db.commit()
    return _ser(s, full=True)


@router.get("/{sid}/documents")
async def supplier_docs(sid: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Document).where(Document.supplier_id==uuid.UUID(sid)).order_by(desc(Document.created_at)))
    docs = r.scalars().all()
    return {"total": len(docs), "documents": [{"id":str(d.id),"nom":d.nom_fichier,"type":str(d.type_document),"statut":str(d.statut),"montant_ttc":d.montant_ttc,"date":d.date_document} for d in docs]}


@router.post("/autofill-from-curated", summary="Auto-fill CRM depuis zone Curated")
async def autofill_crm(db: AsyncSession = Depends(get_db)):
    """Parcourt les documents en zone Curated et met à jour les fiches fournisseurs."""
    from app.models.models import DataZone
    from app.services.minio_service import get_curated
    r = await db.execute(select(Document).where(Document.zone_actuelle == DataZone.CURATED).where(Document.supplier_id == None).where(Document.numero_siren != None))
    docs = r.scalars().all()
    updated = 0
    for doc in docs:
        # Trouver ou créer fournisseur
        res = await db.execute(select(Supplier).where(Supplier.siren == doc.numero_siren))
        sup = res.scalar_one_or_none()
        if not sup:
            sup = Supplier(
                nom=doc.nom_fournisseur or "Inconnu",
                siren=doc.numero_siren, siret_siege=doc.numero_siret,
                numero_tva=doc.numero_tva, iban=doc.iban,
            )
            db.add(sup)
            await db.flush()
        doc.supplier_id = sup.id
        updated += 1
    await db.commit()
    return {"updated": updated, "message": f"{updated} document(s) liés à leur fournisseur"}


def _ser(s: Supplier, full=False) -> dict:
    d = {"id":str(s.id),"nom":s.nom,"siren":s.siren,"siret_siege":s.siret_siege,
         "ville":s.ville,"score_conformite":s.score_conformite,"est_blackliste":s.est_blackliste,
         "attestation_urssaf_valide":s.attestation_urssaf_valide,
         "attestation_fiscale_valide":s.attestation_fiscale_valide,
         "created_at":s.created_at.isoformat() if s.created_at else None}
    if full:
        d.update({"numero_tva":s.numero_tva,"iban":s.iban,"bic":s.bic,"adresse":s.adresse,
                  "code_postal":s.code_postal,"pays":s.pays,"email":s.email,"telephone":s.telephone,
                  "forme_juridique":s.forme_juridique,"code_naf":s.code_naf,
                  "motif_blacklist":s.motif_blacklist,"kbis_date":s.kbis_date,
                  "attestation_urssaf_date_exp":s.attestation_urssaf_date_exp,
                  "date_creation_entreprise":s.date_creation_entreprise})
    return d
