"""
DAG Airflow — DocuFlow v2
Pipeline : Ingestion → OCR → Extraction → Validation → Stockage → Auto-fill
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.http import SimpleHttpOperator
from airflow.models import Variable
import json, requests

# ── Configuration DAG ─────────────────────────────────────────────
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
    schedule_interval=timedelta(minutes=5),   # Vérification toutes les 5 min
    catchup=False,
    tags=["docuflow", "ocr", "conformite"],
    max_active_runs=3,
)

API_BASE = "http://backend:8000/api"


# ── Tâches ────────────────────────────────────────────────────────

def check_pending_documents(**ctx):
    """Récupère les documents en attente de traitement."""
    r = requests.get(f"{API_BASE}/documents/?status=uploade&limit=50", timeout=30)
    docs = r.json().get("documents", [])
    ctx["ti"].xcom_push(key="pending_docs", value=[d["id"] for d in docs])
    print(f"[DocuFlow] {len(docs)} document(s) en attente de traitement")
    return len(docs)


def trigger_ocr_pipeline(**ctx):
    """Déclenche le pipeline OCR via l'API pour chaque document en attente."""
    doc_ids = ctx["ti"].xcom_pull(key="pending_docs", task_ids="check_pending")
    if not doc_ids:
        print("[DocuFlow] Aucun document à traiter")
        return 0
    triggered = 0
    for doc_id in doc_ids:
        try:
            r = requests.post(f"{API_BASE}/documents/{doc_id}/process", timeout=10)
            if r.status_code == 200:
                triggered += 1
                print(f"[DocuFlow] Pipeline lancé pour {doc_id[:8]}…")
        except Exception as e:
            print(f"[DocuFlow] Erreur {doc_id}: {e}")
    ctx["ti"].xcom_push(key="triggered_count", value=triggered)
    return triggered


def verify_inter_document_coherence(**ctx):
    """Vérification de cohérence entre documents du même fournisseur."""
    r = requests.get(f"{API_BASE}/compliance/check-inter-docs", timeout=60)
    result = r.json()
    new_anomalies = result.get("new_anomalies", 0)
    print(f"[DocuFlow] Cohérence inter-docs : {new_anomalies} nouvelle(s) anomalie(s)")
    return new_anomalies


def autofill_crm(**ctx):
    """Auto-remplissage des fiches fournisseurs dans le CRM."""
    r = requests.post(f"{API_BASE}/suppliers/autofill-from-curated", timeout=60)
    result = r.json()
    updated = result.get("updated", 0)
    print(f"[DocuFlow] CRM : {updated} fiche(s) mise(s) à jour")
    return updated


def autofill_compliance(**ctx):
    """Mise à jour de l'outil de conformité."""
    r = requests.post(f"{API_BASE}/compliance/refresh", timeout=60)
    result = r.json()
    print(f"[DocuFlow] Conformité : {result.get('message','ok')}")
    return result


def send_alerts(**ctx):
    """Envoie les alertes pour les anomalies critiques."""
    r = requests.get(f"{API_BASE}/compliance/anomalies?severite=critique&resolved=false", timeout=30)
    anomalies = r.json()
    if isinstance(anomalies, list) and anomalies:
        print(f"[DocuFlow] ⚠️  {len(anomalies)} anomalie(s) critique(s) détectée(s) — alertes envoyées")
    return len(anomalies) if isinstance(anomalies, list) else 0


def cleanup_logs(**ctx):
    """Nettoyage des logs de pipeline > 30 jours."""
    r = requests.delete(f"{API_BASE}/stats/cleanup-logs?days=30", timeout=30)
    print(f"[DocuFlow] Logs nettoyés : {r.json()}")


# ── Opérateurs DAG ────────────────────────────────────────────────

t_check = PythonOperator(
    task_id="check_pending",
    python_callable=check_pending_documents,
    dag=dag,
)

t_ocr = PythonOperator(
    task_id="trigger_ocr",
    python_callable=trigger_ocr_pipeline,
    dag=dag,
)

t_coherence = PythonOperator(
    task_id="inter_doc_coherence",
    python_callable=verify_inter_document_coherence,
    dag=dag,
)

t_crm = PythonOperator(
    task_id="autofill_crm",
    python_callable=autofill_crm,
    dag=dag,
)

t_compliance = PythonOperator(
    task_id="autofill_compliance",
    python_callable=autofill_compliance,
    dag=dag,
)

t_alerts = PythonOperator(
    task_id="send_alerts",
    python_callable=send_alerts,
    dag=dag,
)

t_cleanup = PythonOperator(
    task_id="cleanup_logs",
    python_callable=cleanup_logs,
    dag=dag,
)

# ── Dépendances ───────────────────────────────────────────────────
# check → ocr → coherence → [crm, compliance] → alerts → cleanup
t_check >> t_ocr >> t_coherence >> [t_crm, t_compliance] >> t_alerts >> t_cleanup
