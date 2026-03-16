"""
DAG Airflow — DocuFlow v2
Pipeline : Ingestion → OCR → Extraction → Validation → Stockage → Auto-fill
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

default_args = {
    "owner":            "docuflow",
    "depends_on_past":  False,
    "start_date":       datetime(2026, 3, 16),
    "email_on_failure": False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=1),
}

dag = DAG(
    dag_id="docuflow_pipeline",
    default_args=default_args,
    description="Pipeline traitement automatique documents administratifs",
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=["docuflow", "ocr", "conformite"],
    max_active_runs=3,
)

API_BASE = "http://backend:8000/api"


def check_pending_documents(**ctx):
    try:
        r = requests.get(f"{API_BASE}/documents/?status=uploade&limit=50", timeout=30)
        docs = r.json().get("documents", [])
        ctx["ti"].xcom_push(key="pending_docs", value=[d["id"] for d in docs])
        print(f"[DocuFlow] {len(docs)} document(s) en attente")
        return len(docs)
    except Exception as e:
        print(f"[DocuFlow] Erreur check_pending: {e}")
        return 0


def trigger_ocr_pipeline(**ctx):
    doc_ids = ctx["ti"].xcom_pull(key="pending_docs", task_ids="check_pending") or []
    triggered = 0
    for doc_id in doc_ids:
        try:
            r = requests.post(f"{API_BASE}/documents/{doc_id}/process", timeout=10)
            if r.status_code == 200:
                triggered += 1
                print(f"[DocuFlow] Pipeline lancé: {doc_id[:8]}")
        except Exception as e:
            print(f"[DocuFlow] Erreur trigger {doc_id}: {e}")
    return triggered


def verify_inter_document_coherence(**ctx):
    try:
        r = requests.get(f"{API_BASE}/compliance/check-inter-docs", timeout=60)
        result = r.json()
        n = result.get("new_anomalies", 0)
        print(f"[DocuFlow] Inter-docs: {n} anomalie(s)")
        return n
    except Exception as e:
        print(f"[DocuFlow] Erreur inter-docs: {e}")
        return 0


def autofill_crm(**ctx):
    try:
        r = requests.post(f"{API_BASE}/suppliers/autofill-from-curated", timeout=60)
        n = r.json().get("updated", 0)
        print(f"[DocuFlow] CRM: {n} fiche(s) mise(s) à jour")
        return n
    except Exception as e:
        print(f"[DocuFlow] Erreur autofill CRM: {e}")
        return 0


def autofill_compliance(**ctx):
    try:
        r = requests.post(f"{API_BASE}/compliance/refresh", timeout=60)
        print(f"[DocuFlow] Conformité: {r.json().get('message','ok')}")
    except Exception as e:
        print(f"[DocuFlow] Erreur refresh conformité: {e}")


def send_alerts(**ctx):
    try:
        r = requests.get(f"{API_BASE}/compliance/anomalies?severite=critique&resolved=false", timeout=30)
        anomalies = r.json()
        n = len(anomalies) if isinstance(anomalies, list) else 0
        if n > 0:
            print(f"[DocuFlow] ⚠️  {n} anomalie(s) critique(s) détectée(s)")
        return n
    except Exception as e:
        print(f"[DocuFlow] Erreur alertes: {e}")
        return 0


def cleanup_logs(**ctx):
    try:
        r = requests.delete(f"{API_BASE}/stats/cleanup-logs?days=30", timeout=30)
        print(f"[DocuFlow] Cleanup: {r.json()}")
    except Exception as e:
        print(f"[DocuFlow] Erreur cleanup: {e}")


t_check      = PythonOperator(task_id="check_pending",        python_callable=check_pending_documents,      dag=dag)
t_ocr        = PythonOperator(task_id="trigger_ocr",          python_callable=trigger_ocr_pipeline,         dag=dag)
t_coherence  = PythonOperator(task_id="inter_doc_coherence",  python_callable=verify_inter_document_coherence, dag=dag)
t_crm        = PythonOperator(task_id="autofill_crm",         python_callable=autofill_crm,                 dag=dag)
t_compliance = PythonOperator(task_id="autofill_compliance",  python_callable=autofill_compliance,           dag=dag)
t_alerts     = PythonOperator(task_id="send_alerts",          python_callable=send_alerts,                   dag=dag)
t_cleanup    = PythonOperator(task_id="cleanup_logs",         python_callable=cleanup_logs,                  dag=dag)

t_check >> t_ocr >> t_coherence >> [t_crm, t_compliance] >> t_alerts >> t_cleanup
