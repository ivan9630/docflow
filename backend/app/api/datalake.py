"""API Data Lake"""
from fastapi import APIRouter
from app.services.minio_service import datalake_stats
router = APIRouter()

@router.get("/stats")
def stats():
    return datalake_stats()

@router.get("/{zone}")
def list_objects(zone: str):
    from fastapi import HTTPException
    from minio import Minio
    import os
    if zone not in ["raw","clean","curated"]: raise HTTPException(400, "Zone invalide")
    c = Minio(os.getenv("MINIO_ENDPOINT","localhost:9000"),
              access_key=os.getenv("MINIO_ACCESS_KEY","docuflow"),
              secret_key=os.getenv("MINIO_SECRET_KEY","docuflow123"), secure=False)
    try:
        objs = list(c.list_objects(zone, recursive=True))
        return {"zone":zone,"objects":[{"name":o.object_name,"size":o.size,"modified":o.last_modified.isoformat() if o.last_modified else None} for o in objs]}
    except Exception as e:
        return {"zone":zone,"objects":[],"error":str(e)}
