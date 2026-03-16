"""API Airflow Trigger"""
from fastapi import APIRouter
import httpx, os
router = APIRouter()
AIRFLOW_URL = os.getenv("AIRFLOW_URL","http://airflow-webserver:8080")

@router.post("/trigger/{dag_id}")
async def trigger_dag(dag_id: str, conf: dict = {}):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns",
                             json={"conf": conf},
                             auth=("admin","docuflow123"))
            return r.json()
    except Exception as e:
        return {"error": str(e), "message": "Airflow non disponible (pipeline Celery actif)"}

@router.get("/status/{dag_id}")
async def dag_status(dag_id: str):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{AIRFLOW_URL}/api/v1/dags/{dag_id}", auth=("admin","docuflow123"))
            return r.json()
    except Exception as e:
        return {"error": str(e)}
