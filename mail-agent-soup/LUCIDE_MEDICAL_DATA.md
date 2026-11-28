# LUCIDE — medical mail agent
Staging only; original Lucide repository not located. Do not connect real patient inboxes before approval.
## Source registry
- https://huggingface.co/datasets/HealthDataHub/PARCOMED — commercial-compatible collection, review constituent licenses and attribution; use selected French texts only.
- https://health-data-hub.fr/page/projet-partages — synthetic clinical reports, verify individual corpus rights before use; research-only datasets excluded from commercial pipeline.
- https://huggingface.co/datasets/qanastek/frenchmedmcqa — Apache-2.0, 3105 pharmacy exam questions; preserve official test split, auxiliary evaluation.
- https://huggingface.co/datasets/ANR-MALADES/MediQAl — CC BY 4.0, verify revision and attribution; auxiliary evaluation.
- https://www.data.gouv.fr/datasets/base-de-donnees-publique-des-medicaments-base-officielle — open license; RAG, not prescriptions.
- https://www.data.gouv.fr/fr/datasets/textes-des-publications-de-la-has-7/ — RAG, verify current validity and attribution.
- https://www.lisn.upsaclay.fr/corpus-software/cas-cliniques-annotes-en-entites-nommees-et-informations-demographiques/ — extraction research corpus, no ingestion until license review.
## Pipeline
Pin revisions, record licenses per document, deduplicate before split, preserve provenance and official test sets. Separate task SFT from medical knowledge RAG. Create synthetic French medical inbox scenarios, clinician-reviewed labels, no real identifiers. Train only on reviewed train split. Keep test scenarios separate by template and source. Compare baseline and adapter.
## Output contract
document_type, summary, extracted_fields with evidence, patient_match_status (unverified by default), review_required (always true for clinical documents), explicit_sender_urgency, proposed_admin_action, source_references. Never diagnose, prescribe, send, assign low clinical urgency, or merge patient records automatically.
## Deployment gate
MSSante integration via authorized operator; access controls, local encrypted storage, audit, retention, no external inference or public Git patient data. Review RGPD legal basis and health-data hosting obligations with cabinet. Human validation of all clinical outputs. Gmail demo connector is synthetic/test only.
## Evaluation
Document classification macro F1; exact extraction accuracy; unsupported claim rate; missed explicit urgent flags; wrong patient matches; prompt injection tests. Zero observed critical errors on reviewed safety test set is necessary but not sufficient for deployment.
