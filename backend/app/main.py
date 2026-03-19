"""
DocuFlow v2 — Plateforme de traitement automatique de documents administratifs
Hackathon 2026
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.api import documents, suppliers, compliance, datalake, stats, airflow_trigger, auth
from app.db.database import create_tables, AsyncSessionLocal
from app.services.minio_service import init_minio_buckets

logger = structlog.get_logger()


async def seed_users():
    """Crée les comptes par défaut s'ils n'existent pas."""
    from sqlalchemy import select
    from app.models.models import User
    from app.services.auth_service import hash_password

    defaults = [
        ("admin",        "admin123",  "Administrateur",       "admin"),
        ("gestionnaire", "gest123",   "Gestionnaire CRM",     "gestionnaire"),
        ("conformite",   "conf123",   "Agent Conformité",     "conformite"),
    ]
    async with AsyncSessionLocal() as db:
        for username, password, nom, role in defaults:
            r = await db.execute(select(User).where(User.username == username))
            if not r.scalar_one_or_none():
                db.add(User(
                    username=username,
                    hashed_password=hash_password(password),
                    nom_complet=nom,
                    role=role,
                ))
                logger.info(f"👤 Utilisateur créé : {username} ({role})")
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DocuFlow v2 démarrage…")
    await create_tables()
    await init_minio_buckets()
    await seed_users()
    logger.info("✅ DocuFlow v2 prêt !")
    yield
    logger.info("🛑 DocuFlow v2 arrêt")


app = FastAPI(
    title="DocuFlow v2 API",
    description="""
## DocuFlow — Traitement Automatique de Documents Administratifs

### Pipeline complet :
1. **Upload** → Stockage RAW (MinIO)
2. **OCR** → Tesseract + OpenCV preprocessing
3. **NER** → spaCy + extraction entités
4. **Classification IA** → Claude claude-opus-4-5
5. **Vérification** → Cohérence inter-documents
6. **Stockage** → Architecture Médaillon (Raw/Clean/Curated)
7. **Auto-fill** → CRM + Outil Conformité

### Architecture Data Lake :
- 🟤 **RAW** : fichiers bruts immuables
- ⚪ **CLEAN** : texte OCR + JSON extrait
- 🟡 **CURATED** : données enrichies, prêtes métier
    """,
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,              prefix="/api/auth",       tags=["🔑 Auth"])
app.include_router(documents.router,        prefix="/api/documents",  tags=["📄 Documents"])
app.include_router(suppliers.router,        prefix="/api/suppliers",  tags=["🏢 Fournisseurs"])
app.include_router(compliance.router,       prefix="/api/compliance", tags=["🔒 Conformité"])
app.include_router(datalake.router,         prefix="/api/datalake",   tags=["💾 Data Lake"])
app.include_router(stats.router,            prefix="/api/stats",      tags=["📊 Statistiques"])
app.include_router(airflow_trigger.router,  prefix="/api/airflow",    tags=["🔄 Airflow"])


@app.get("/health", tags=["Système"])
async def health():
    return {"status": "ok", "service": "DocuFlow API v2", "version": "2.0.0"}
