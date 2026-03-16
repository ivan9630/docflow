"""Service Data Lake MinIO — Zones Raw / Clean / Curated"""
import os, io, json, hashlib
from minio import Minio
from minio.error import S3Error
import structlog

logger = structlog.get_logger()

ENDPOINT   = os.getenv("MINIO_ENDPOINT", "localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "docuflow")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "docuflow123")

BUCKET_RAW     = "raw"
BUCKET_CLEAN   = "clean"
BUCKET_CURATED = "curated"


def _client() -> Minio:
    return Minio(ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)


async def init_minio_buckets():
    c = _client()
    for b in [BUCKET_RAW, BUCKET_CLEAN, BUCKET_CURATED]:
        try:
            if not c.bucket_exists(b):
                c.make_bucket(b)
                logger.info(f"Bucket créé: {b}")
        except S3Error as e:
            logger.error(f"MinIO bucket {b}: {e}")


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ── RAW ZONE ─────────────────────────────────────────────────────

def store_raw(doc_id: str, filename: str, content: bytes) -> str:
    """Stocke le fichier brut immuable en zone RAW."""
    c = _client()
    key = f"{doc_id}/original/{filename}"
    c.put_object(BUCKET_RAW, key, io.BytesIO(content), len(content),
                 metadata={"doc_id": doc_id, "sha256": sha256(content), "zone": "raw"})
    return key


# ── CLEAN ZONE ───────────────────────────────────────────────────

def store_clean(doc_id: str, ocr_result: dict, entities: dict) -> str:
    """Stocke le texte OCR + entités extraites en zone CLEAN."""
    c = _client()
    key = f"{doc_id}/clean/data.json"
    payload = {"doc_id": doc_id, "zone": "clean", "ocr": ocr_result, "entities": entities}
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode()
    c.put_object(BUCKET_CLEAN, key, io.BytesIO(data), len(data),
                 content_type="application/json")
    return key


# ── CURATED ZONE ─────────────────────────────────────────────────

def store_curated(doc_id: str, full_payload: dict) -> str:
    """Stocke les données enrichies, prêtes pour CRM/conformité."""
    c = _client()
    key = f"{doc_id}/curated/data.json"
    full_payload["zone"] = "curated"
    data = json.dumps(full_payload, ensure_ascii=False, indent=2).encode()
    c.put_object(BUCKET_CURATED, key, io.BytesIO(data), len(data),
                 content_type="application/json")
    return key


# ── READ ─────────────────────────────────────────────────────────

def get_raw(key: str) -> bytes:
    return _client().get_object(BUCKET_RAW, key).read()

def get_clean(key: str) -> dict:
    return json.loads(_client().get_object(BUCKET_CLEAN, key).read())

def get_curated(key: str) -> dict:
    return json.loads(_client().get_object(BUCKET_CURATED, key).read())


# ── STATS ────────────────────────────────────────────────────────

def datalake_stats() -> dict:
    c = _client()
    stats = {}
    for zone, bucket in [("raw", BUCKET_RAW), ("clean", BUCKET_CLEAN), ("curated", BUCKET_CURATED)]:
        try:
            objs = list(c.list_objects(bucket, recursive=True))
            total = sum(o.size or 0 for o in objs)
            stats[zone] = {"count": len(objs), "size_bytes": total, "size_mb": round(total/1024/1024, 2)}
        except Exception:
            stats[zone] = {"count": 0, "size_bytes": 0, "size_mb": 0}
    return stats
