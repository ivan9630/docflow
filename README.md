# 🚀 DocuFlow v2 — Traitement Automatique de Documents Administratifs

> **Hackathon 2026 · Semaine du 16–20 mars**
> Thème : Traitement automatique de documents administratifs

---

## 🏗️ Architecture Technique

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DOCUFLOW v2 ARCHITECTURE                     │
│                                                                      │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌────────────────┐  │
│  │ Upload  │───▶│  Celery  │───▶│ OCR+NER  │───▶│ Claude IA      │  │
│  │ Multi   │    │ Worker   │    │ Tesseract│    │ Classification │  │
│  │ Docs    │    │          │    │ spaCy    │    │ Fraude         │  │
│  └─────────┘    └──────────┘    └──────────┘    └────────────────┘  │
│                                                          │            │
│  ┌──────────────────────────────────────────────────────▼──────┐    │
│  │                  DATA LAKE — Architecture Médaillon          │    │
│  │   🟤 RAW (MinIO)  →  ⚪ CLEAN (MinIO)  →  🟡 CURATED (MinIO)│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                           │                     │                    │
│               ┌───────────▼──────┐   ┌──────────▼──────────┐       │
│               │   CRM React      │   │  Conformité React    │       │
│               │   :3000          │   │  :3000/compliance    │       │
│               └──────────────────┘   └─────────────────────┘       │
│                                                                      │
│  🌊 Airflow DAG   🌸 Celery Flower   💾 MinIO   🐘 PostgreSQL       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🧱 Stack Technique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Backend API** | FastAPI 0.111 + Python 3.12 | REST API async |
| **Pipeline async** | Celery + Redis | Traitement documents |
| **Orchestration** | Apache Airflow 2.9 | DAG scheduling |
| **OCR** | Tesseract 5 + pdfplumber + OpenCV | Extraction texte |
| **NER** | spaCy `fr_core_news_sm` | Extraction entités |
| **IA / LLM** | Claude claude-opus-4-5 (Anthropic) | Classification, fraude, enrichissement |
| **Base de données** | PostgreSQL 16 | Stockage structuré |
| **Data Lake** | MinIO (S3-compatible) | Raw / Clean / Curated |
| **Frontend** | React 18 + Vite + Tailwind | Interface MERN-like |
| **Monitoring** | Celery Flower | Supervision workers |
| **Conteneurs** | Docker Compose | Orchestration 10 services |

---

## 🚀 Démarrage Rapide

### Prérequis
```bash
docker --version    # >= 24.0
docker compose version  # >= 2.20
python --version    # >= 3.10 (pour le générateur de données)
```

### 1. Obtenir la clé API Anthropic
```
1. Aller sur https://console.anthropic.com
2. Créer un compte (5$ de crédits gratuits)
3. Menu "API Keys" → "Create Key"
4. Copier la clé (commence par sk-ant-api03-...)
```

### 2. Configurer l'environnement
```bash
cd docuflow_v2
cp .env.example .env
# Éditer .env et remplacer ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_ICI
notepad .env   # Windows
```

### 3. Lancer Docker
```bash
# S'assurer que Docker Desktop est démarré
docker compose up --build -d

# Voir les logs
docker compose logs -f backend
docker compose logs -f worker
```

### 4. Générer le jeu de données de test
```bash
cd data_generator
pip install -r requirements.txt
python generate_dataset.py --count 100 --output ./dataset
# Puis uploader les images via l'interface web
```

---

## 🌐 Interfaces

| Service | URL | Identifiants |
|---------|-----|-------------|
| **Application principale** | http://localhost:3000 | — |
| **API Swagger** | http://localhost:8000/docs | — |
| **Airflow UI** | http://localhost:8080 | admin / docuflow123 |
| **Celery Flower** | http://localhost:5555 | — |
| **MinIO Console** | http://localhost:9001 | docuflow / docuflow123 |
| **PostgreSQL** | localhost:5432 | docuflow / docuflow |

---

## 📋 Fonctionnalités

### i) Upload Multi-Documents
- Drag & drop jusqu'à 20 fichiers simultanément
- Formats : PDF, JPEG, PNG, TIFF (50 MB max/fichier)
- Validation MIME par magic bytes (pas par extension)
- Hash SHA-256 pour déduplication
- Suivi temps réel de la progression (polling SSE)

### ii) Classification Automatique (IA)
Types détectés par **Claude claude-opus-4-5** :
`facture` · `devis` · `bon_commande` · `attestation_urssaf` · `attestation_fiscale` · `kbis` · `rib` · `contrat` · `autre`

Score de confiance 0.0 → 1.0 avec indices de classification.

### iii) OCR Robuste
Pipeline hybride en 2 passes :
1. **pdfplumber** → texte natif (PDFs textuels, confiance ~96%)
2. **Tesseract 5** + prétraitement OpenCV :
   - Conversion niveaux de gris
   - Débruitage (`fastNlMeansDenoising`)
   - Deskew automatique
   - Binarisation Otsu
   - Amélioration netteté

**NER spaCy** (`fr_core_news_sm`) pour : organisations, dates, lieux, personnes

**Extracteurs Regex** spécialisés :
- SIREN (validé par algorithme de Luhn)
- SIRET (14 chiffres)
- TVA intracommunautaire FR
- Montants HT / TVA / TTC
- IBAN / BIC
- Dates d'émission et d'expiration
- Numéros de documents

### iv) Vérification & Détection de Fraude
**Validations locales instantanées :**
- SIRET doit commencer par le SIREN
- Clé TVA FR = (12 + 3×(SIREN mod 97)) mod 97
- TTC = HT × (1 + taux_TVA) [tolérance 0.02€]
- IBAN conforme au référentiel fournisseur

**Détection IA (Claude) :**
- Incohérences inter-documents (même fournisseur)
- Montants aberrants
- Dates expirées (attestations)
- Doublons de numéros de documents
- Patterns de fraude complexes

Score de fraude 0→1, seuil critique à 0.7.

### v) Data Lake — Architecture Médaillon

```
raw/     {doc_id}/original/{filename}      ← Fichier brut immuable
clean/   {doc_id}/clean/data.json          ← OCR + entités JSON
curated/ {doc_id}/curated/data.json        ← Enrichi IA, prêt métier
```

### vi) Frontends Métier (React)
**CRM Fournisseurs** :
- Dashboard KPIs temps réel (recharts)
- Upload multi-fichiers avec progression live
- Table documents avec filtres avancés
- Fiches fournisseurs auto-remplies depuis zone Curated
- Score de conformité visuel

**Outil de Conformité** :
- Alertes classées par sévérité (critique/élevée/moyenne/faible)
- Radar de fraude avec scores
- Vérification cohérence inter-documents
- Résolution des anomalies avec historique
- Gestion blacklist fournisseurs

### vii) Orchestration Airflow
DAG `docuflow_pipeline` (schedule: 5 min) :
```
check_pending → trigger_ocr → inter_doc_coherence 
    → [autofill_crm ‖ autofill_compliance] → send_alerts → cleanup_logs
```

---

## 📁 Structure du Projet

```
docuflow_v2/
├── docker-compose.yml          # 10 services Docker
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile              # Python + Tesseract + spaCy
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI + lifespan
│       ├── celery_app.py       # Pipeline 6 étapes
│       ├── api/
│       │   ├── documents.py    # Upload, list, status, validate
│       │   ├── suppliers.py    # CRM + autofill
│       │   ├── compliance.py   # Anomalies, fraude, inter-docs
│       │   ├── datalake.py     # Stats, explorer zones
│       │   ├── stats.py        # Dashboard KPIs
│       │   └── airflow_trigger.py
│       ├── models/models.py    # SQLAlchemy ORM
│       ├── services/
│       │   ├── ocr_service.py  # OCR + NER + extracteurs
│       │   ├── ai_service.py   # Claude API + validations locales
│       │   └── minio_service.py# Data Lake Raw/Clean/Curated
│       └── db/database.py
│
├── frontend/                   # React 18 + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx             # Router + Sidebar
│   │   ├── api.js              # Axios centralisé
│   │   ├── components/UI.jsx   # Design system
│   │   └── pages/
│   │       ├── Dashboard.jsx
│   │       ├── UploadPage.jsx
│   │       ├── DocumentsPage.jsx
│   │       ├── SuppliersPage.jsx
│   │       ├── CompliancePage.jsx
│   │       ├── DataLakePage.jsx
│   │       └── PipelinePage.jsx
│
├── airflow/
│   └── dags/docuflow_pipeline.py  # DAG complet
│
├── docker/
│   └── init.sql                # PostgreSQL init + vues + données démo
│
└── data_generator/
    ├── generate_dataset.py     # Faker + dégradation scans
    └── requirements.txt
```

---

## 🔌 API Reference

### Documents
```
POST   /api/documents/upload              Upload 1-20 fichiers
GET    /api/documents/                    Liste avec filtres
GET    /api/documents/{id}                Détail complet
GET    /api/documents/{id}/status         Statut pipeline
POST   /api/documents/{id}/process        Relancer pipeline
PATCH  /api/documents/{id}/validate       Valider manuellement
PATCH  /api/documents/{id}/reject         Rejeter
```

### Fournisseurs (CRM)
```
GET    /api/suppliers/                    Liste fournisseurs
POST   /api/suppliers/                    Créer fournisseur
GET    /api/suppliers/{id}                Fiche complète
PATCH  /api/suppliers/{id}                Modifier
GET    /api/suppliers/{id}/documents      Documents du fournisseur
POST   /api/suppliers/autofill-from-curated  Auto-fill depuis zone Curated
```

### Conformité
```
GET    /api/compliance/anomalies          Anomalies (filtre sévérité)
GET    /api/compliance/fraudulent         Documents frauduleux
PATCH  /api/compliance/anomalies/{id}/resolve  Résoudre
GET    /api/compliance/check-inter-docs   Vérification croisée
POST   /api/compliance/refresh            Recalcul scores conformité
```

### Data Lake
```
GET    /api/datalake/stats                Stats par zone
GET    /api/datalake/{zone}               Explorer zone (raw/clean/curated)
```

---

## ❓ Réponses aux Questions Jury

**Pourquoi Claude claude-opus-4-5 plutôt qu'un autre modèle ?**
Claude claude-opus-4-5 excelle en compréhension de documents français complexes, en raisonnement sur les cohérences réglementaires (TVA, SIRET) et produit du JSON structuré fiable. Alternatives possibles : GPT-4o, Gemini Pro — Claude claude-opus-4-5 offre le meilleur rapport qualité/coût pour la classification documentaire.

**Comment scaler à 1 million de documents ?**
- MinIO en cluster distribué (compatible HDFS)
- Celery avec auto-scaling horizontal (K8s + KEDA)
- PostgreSQL → partitionnement par date + read replicas
- Airflow avec CeleryExecutor → KubernetesExecutor
- Cache Redis pour les classifications fréquentes

**Comment gérer de nouveaux champs ?**
Architecture extensible : la zone Curated stocke du JSON schéma-libre. Ajouter un champ = modifier uniquement l'extracteur regex + le prompt Claude, sans migration BDD.

**Comment optimiser la latence ?**
- OCR parallélisé (multi-page PDF)
- Classification IA en batch (Anthropic batch API)
- Cache Redis sur les SIREN déjà vus
- Pre-processing image GPU (OpenCV CUDA)
- CDN pour les assets frontend

---

## 👥 Répartition des Rôles Suggérée

| Étudiant | Rôle | Fichiers clés |
|---------|------|--------------|
| **M1 - 1** | Dataset & tests | `data_generator/generate_dataset.py` |
| **M1 - 2** | OCR & NER | `backend/app/services/ocr_service.py` |
| **M1 - 3** | Frontend React | `frontend/src/pages/` |
| **M2 - 4** | Data Lake | `backend/app/services/minio_service.py` |
| **M2 - 5** | Fraude & conformité | `backend/app/services/ai_service.py`, `api/compliance.py` |
| **M2 - 6** | Airflow & DevOps | `airflow/dags/`, `docker-compose.yml` |

---

*DocuFlow v2 — Automatiser. Vérifier. Conformer.*
*Hackathon 2026 — Équipe DocuFlow*
