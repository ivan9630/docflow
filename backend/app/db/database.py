from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://docuflow:docuflow@localhost:5432/docuflow")
engine = create_async_engine(URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as s:
        try: yield s
        finally: await s.close()
