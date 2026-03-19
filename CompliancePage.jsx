import { useState, useRef, useCallback } from "react";

const SEVERITY_CONFIG = {
  critique: { color: "#ef4444", bg: "#ef444415", label: "CRITIQUE", icon: "🔴" },
  elevee: { color: "#f97316", bg: "#f9731615", label: "ÉLEVÉE", icon: "🟠" },
  moyenne: { color: "#eab308", bg: "#eab30815", label: "MOYENNE", icon: "🟡" },
  faible: { color: "#22c55e", bg: "#22c55e15", label: "FAIBLE", icon: "🟢" },
};

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result.split(",")[1]);
    r.onerror = () => reject(new Error("Lecture fichier échouée"));
    r.readAsDataURL(file);
  });
}

function ScoreGauge({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? "#ef4444" : pct >= 40 ? "#f97316" : "#22c55e";
  const label = pct >= 70 ? "FRAUDE DÉTECTÉE" : pct >= 40 ? "SUSPECT" : "CONFORME";
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <svg width={140} height={140} viewBox="0 0 140 140">
        <circle cx={70} cy={70} r={54} fill="none" stroke="#1e293b" strokeWidth={12} />
        <circle
          cx={70} cy={70} r={54} fill="none"
          stroke={color} strokeWidth={12}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: "stroke-dashoffset 1s ease, stroke 0.5s" }}
        />
        <text x={70} y={65} textAnchor="middle" fill={color} fontSize={28} fontWeight="700" fontFamily="'DM Mono', monospace">{pct}%</text>
        <text x={70} y={85} textAnchor="middle" fill="#64748b" fontSize={10} fontFamily="'DM Mono', monospace">SCORE FRAUDE</text>
      </svg>
      <div style={{
        padding: "4px 14px", borderRadius: 20,
        background: color + "22", color, fontWeight: 700,
        fontSize: 12, letterSpacing: 2, fontFamily: "'DM Mono', monospace",
        border: `1px solid ${color}44`
      }}>
        {label}
      </div>
    </div>
  );
}

function DataField({ label, value, highlight }) {
  if (!value) return null;
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "flex-start",
      padding: "8px 0", borderBottom: "1px solid #1e293b", gap: 12
    }}>
      <span style={{ color: "#64748b", fontSize: 12, fontFamily: "'DM Mono', monospace", flexShrink: 0 }}>{label}</span>
      <span style={{
        color: highlight ? "#60a5fa" : "#e2e8f0", fontSize: 12,
        fontFamily: "'DM Mono', monospace", textAlign: "right", wordBreak: "break-all"
      }}>{value}</span>
    </div>
  );
}

function AnomalyCard({ anomaly, index }) {
  const cfg = SEVERITY_CONFIG[anomaly.severite] || SEVERITY_CONFIG.moyenne;
  return (
    <div style={{
      background: cfg.bg, border: `1px solid ${cfg.color}44`,
      borderLeft: `3px solid ${cfg.color}`,
      borderRadius: 8, padding: "12px 16px", marginBottom: 8,
      animation: `slideIn 0.3s ease ${index * 0.07}s both`
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <span style={{ color: cfg.color, fontSize: 11, fontWeight: 700, letterSpacing: 1.5, fontFamily: "'DM Mono', monospace" }}>
          {cfg.icon} {cfg.label}
        </span>
        <span style={{ color: "#475569", fontSize: 10, fontFamily: "'DM Mono', monospace" }}>{anomaly.type}</span>
      </div>
      <p style={{ color: "#cbd5e1", fontSize: 13, margin: 0 }}>{anomaly.description}</p>
    </div>
  );
}

export default function CompliancePage() {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const analyzeDocument = async (f) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const isImage = f.type.startsWith("image/");
      const isPdf = f.type === "application/pdf";

      let messageContent = [];

      if (isImage) {
        setLoadingStep("🔍 Lecture de l'image...");
        const b64 = await fileToBase64(f);
        messageContent = [
          {
            type: "image",
            source: { type: "base64", media_type: f.type, data: b64 }
          },
          { type: "text", text: buildPrompt(f.name) }
        ];
      } else if (isPdf) {
        setLoadingStep("📄 Extraction PDF...");
        const b64 = await fileToBase64(f);
        messageContent = [
          {
            type: "document",
            source: { type: "base64", media_type: "application/pdf", data: b64 }
          },
          { type: "text", text: buildPrompt(f.name) }
        ];
      } else {
        // Texte brut
        setLoadingStep("📝 Lecture du fichier...");
        const text = await f.text();
        messageContent = [{ type: "text", text: `Voici le contenu du document "${f.name}":\n\n${text}\n\n${buildPrompt(f.name)}` }];
      }

      setLoadingStep("🤖 Analyse IA en cours...");

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{ role: "user", content: messageContent }],
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error?.message || `Erreur API: ${response.status}`);
      }

      const data = await response.json();
      setLoadingStep("✅ Traitement des résultats...");

      const raw = data.content.map(i => i.text || "").join("\n");
      const clean = raw.replace(/```json|```/g, "").trim();

      let parsed;
      // Try to extract JSON from the response
      const jsonMatch = clean.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        parsed = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error("Réponse IA invalide — JSON non trouvé");
      }

      setResult({ ...parsed, filename: f.name, size: f.size });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  const buildPrompt = (filename) => `
Tu es un expert en conformité documentaire et détection de fraude pour des documents administratifs français.

Analyse ce document et retourne UNIQUEMENT un JSON valide (sans markdown, sans texte avant ou après) avec cette structure exacte:

{
  "type_document": "facture|devis|bon_commande|attestation_urssaf|attestation_fiscale|kbis|rib|contrat|autre",
  "confiance_classification": 0.95,
  "score_fraude": 0.12,
  "verdict": "CONFORME|SUSPECT|FRAUDE_DETECTEE",
  "resume": "Résumé court de 1-2 phrases sur le document",
  "entites": {
    "fournisseur": "nom de l'entreprise émettrice",
    "client": "nom du destinataire si présent",
    "siren": "9 chiffres si trouvé",
    "siret": "14 chiffres si trouvé",
    "tva_intracom": "FR + 11 chars si trouvé",
    "montant_ht": "montant en euros si trouvé",
    "montant_tva": "montant en euros si trouvé",
    "montant_ttc": "montant en euros si trouvé",
    "iban": "si trouvé",
    "bic": "si trouvé",
    "date_emission": "JJ/MM/AAAA si trouvée",
    "date_echeance": "JJ/MM/AAAA si trouvée",
    "numero_document": "numéro de facture/devis/etc si trouvé",
    "adresse": "adresse si trouvée"
  },
  "anomalies": [
    {
      "type": "COHERENCE_TVA|SIRET_INVALIDE|DATE_EXPIREE|MONTANT_ABERRANT|DOUBLON|PATTERN_FRAUDE|FORMAT_INVALIDE",
      "severite": "critique|elevee|moyenne|faible",
      "description": "Description précise de l'anomalie détectée"
    }
  ],
  "validations": {
    "siret_valide": true,
    "tva_coherente": true,
    "montants_coherents": true,
    "dates_valides": true,
    "iban_format_valide": null
  },
  "recommandation": "Action recommandée en une phrase"
}

Si une donnée n'est pas trouvée, mets null. Le score_fraude va de 0 (aucun risque) à 1 (fraude certaine).
Sois rigoureux dans la détection : vérifie la clé TVA FR = (12 + 3×(SIREN mod 97)) mod 97, vérifie que SIRET commence par SIREN, vérifie TTC ≈ HT × (1 + taux).
Nom du fichier : ${filename}
`;

  const handleFile = (f) => {
    if (!f) return;
    const allowed = ["application/pdf", "image/jpeg", "image/png", "image/tiff", "image/webp", "text/plain"];
    if (!allowed.includes(f.type) && !f.name.match(/\.(pdf|jpg|jpeg|png|tiff|txt)$/i)) {
      setError("Format non supporté. Utilisez PDF, JPEG, PNG, TIFF ou TXT.");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError("Fichier trop volumineux (max 50 MB).");
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
    analyzeDocument(f);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const anomaliesCritiques = result?.anomalies?.filter(a => a.severite === "critique") || [];
  const anomaliesElevees = result?.anomalies?.filter(a => a.severite === "elevee") || [];
  const anomaliesMoyennes = result?.anomalies?.filter(a => a.severite === "moyenne") || [];
  const anomalesFaibles = result?.anomalies?.filter(a => a.severite === "faible") || [];

  return (
    <div style={{
      minHeight: "100vh", background: "#020817",
      fontFamily: "'DM Mono', 'Fira Code', monospace",
      color: "#e2e8f0", padding: "0"
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&display=swap');
        @keyframes slideIn { from { opacity:0; transform:translateX(-10px) } to { opacity:1; transform:translateX(0) } }
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:.5 } }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }
        ::-webkit-scrollbar { width:6px } ::-webkit-scrollbar-track { background:#0f172a }
        ::-webkit-scrollbar-thumb { background:#334155; border-radius:3px }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: "1px solid #1e293b", padding: "16px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "#0a0f1e"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18
          }}>⚖️</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 500, letterSpacing: 1 }}>DOCUFLOW</div>
            <div style={{ fontSize: 10, color: "#475569", letterSpacing: 2 }}>CONFORMITÉ & DÉTECTION FRAUDE</div>
          </div>
        </div>
        <div style={{
          fontSize: 10, color: "#334155", letterSpacing: 1,
          padding: "4px 10px", border: "1px solid #1e293b", borderRadius: 4
        }}>
          v2.0 · ANALYSE IA TEMPS RÉEL
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px" }}>

        {/* Upload Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !loading && inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragging ? "#3b82f6" : loading ? "#8b5cf6" : "#1e293b"}`,
            borderRadius: 12, padding: "40px 24px", textAlign: "center",
            cursor: loading ? "wait" : "pointer",
            background: dragging ? "#3b82f608" : loading ? "#8b5cf608" : "#0a0f1e",
            transition: "all 0.2s", marginBottom: 32,
            position: "relative", overflow: "hidden"
          }}
        >
          <input ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.tiff,.txt"
            style={{ display: "none" }}
            onChange={(e) => handleFile(e.target.files[0])}
          />

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
              <div style={{
                width: 40, height: 40, border: "3px solid #1e293b",
                borderTop: "3px solid #8b5cf6", borderRadius: "50%",
                animation: "spin 1s linear infinite"
              }} />
              <div style={{ color: "#8b5cf6", fontSize: 14, letterSpacing: 1 }}>{loadingStep}</div>
              <div style={{ color: "#475569", fontSize: 11 }}>Analyse Claude IA en cours...</div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📂</div>
              <div style={{ fontSize: 15, color: "#94a3b8", marginBottom: 6 }}>
                Déposer un document ou <span style={{ color: "#3b82f6" }}>parcourir</span>
              </div>
              <div style={{ fontSize: 11, color: "#334155", letterSpacing: 1 }}>
                PDF · JPEG · PNG · TIFF · TXT — MAX 50 MB
              </div>
              {file && !loading && (
                <div style={{
                  marginTop: 12, fontSize: 11, color: "#64748b",
                  padding: "4px 12px", background: "#1e293b", borderRadius: 20, display: "inline-block"
                }}>
                  📎 {file.name} ({formatSize(file.size)})
                </div>
              )}
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: "#ef444415", border: "1px solid #ef444444", borderLeft: "3px solid #ef4444",
            borderRadius: 8, padding: "14px 16px", marginBottom: 24, color: "#fca5a5", fontSize: 13
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div style={{ animation: "fadeIn 0.4s ease" }}>

            {/* Top summary bar */}
            <div style={{
              background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 12,
              padding: "20px 24px", marginBottom: 24,
              display: "flex", alignItems: "center", justifyContent: "space-between",
              flexWrap: "wrap", gap: 16
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <ScoreGauge score={result.score_fraude || 0} />
                <div>
                  <div style={{ fontSize: 11, color: "#475569", letterSpacing: 1.5, marginBottom: 4 }}>DOCUMENT ANALYSÉ</div>
                  <div style={{ fontSize: 18, color: "#e2e8f0", fontWeight: 500 }}>{result.filename}</div>
                  <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>
                    {result.type_document?.toUpperCase()} · confiance {Math.round((result.confiance_classification || 0) * 100)}%
                  </div>
                  <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 8, maxWidth: 400 }}>{result.resume}</div>
                </div>
              </div>
              <div style={{
                padding: "8px 20px", borderRadius: 8, fontSize: 11, fontWeight: 700, letterSpacing: 2,
                background: result.verdict === "CONFORME" ? "#22c55e15" : result.verdict === "FRAUDE_DETECTEE" ? "#ef444415" : "#f9731615",
                color: result.verdict === "CONFORME" ? "#22c55e" : result.verdict === "FRAUDE_DETECTEE" ? "#ef4444" : "#f97316",
                border: `1px solid ${result.verdict === "CONFORME" ? "#22c55e44" : result.verdict === "FRAUDE_DETECTEE" ? "#ef444444" : "#f9731644"}`,
              }}>
                {result.verdict?.replace("_", " ")}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

              {/* Entités extraites */}
              <div style={{ background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 11, color: "#475569", letterSpacing: 2, marginBottom: 16 }}>
                  🔎 ENTITÉS EXTRAITES
                </div>
                {result.entites && Object.entries(result.entites).map(([k, v]) =>
                  v ? <DataField key={k} label={k.replace(/_/g, " ").toUpperCase()} value={v} /> : null
                )}
                {!result.entites || Object.values(result.entites).every(v => !v) ? (
                  <div style={{ color: "#475569", fontSize: 12 }}>Aucune entité détectée</div>
                ) : null}
              </div>

              {/* Validations + Anomalies */}
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

                {/* Validations */}
                <div style={{ background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
                  <div style={{ fontSize: 11, color: "#475569", letterSpacing: 2, marginBottom: 16 }}>
                    ✅ VALIDATIONS LOCALES
                  </div>
                  {result.validations && Object.entries(result.validations).map(([k, v]) => (
                    <div key={k} style={{
                      display: "flex", justifyContent: "space-between",
                      padding: "6px 0", borderBottom: "1px solid #1e293b"
                    }}>
                      <span style={{ color: "#64748b", fontSize: 11 }}>{k.replace(/_/g, " ").toUpperCase()}</span>
                      <span style={{
                        fontSize: 11, fontWeight: 700,
                        color: v === null ? "#475569" : v ? "#22c55e" : "#ef4444"
                      }}>
                        {v === null ? "N/A" : v ? "✓ VALIDE" : "✗ INVALIDE"}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Recommandation */}
                {result.recommandation && (
                  <div style={{
                    background: "#0a0f1e", border: "1px solid #3b82f644",
                    borderLeft: "3px solid #3b82f6",
                    borderRadius: 12, padding: 16
                  }}>
                    <div style={{ fontSize: 11, color: "#3b82f6", letterSpacing: 2, marginBottom: 8 }}>
                      💡 RECOMMANDATION
                    </div>
                    <div style={{ fontSize: 13, color: "#94a3b8" }}>{result.recommandation}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Anomalies */}
            {result.anomalies?.length > 0 && (
              <div style={{ background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginTop: 20 }}>
                <div style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16
                }}>
                  <div style={{ fontSize: 11, color: "#475569", letterSpacing: 2 }}>
                    ⚠️ ANOMALIES DÉTECTÉES ({result.anomalies.length})
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {anomaliesCritiques.length > 0 && <span style={{ fontSize: 10, color: "#ef4444", background: "#ef444415", padding: "2px 8px", borderRadius: 10 }}>{anomaliesCritiques.length} critique{anomaliesCritiques.length > 1 ? "s" : ""}</span>}
                    {anomaliesElevees.length > 0 && <span style={{ fontSize: 10, color: "#f97316", background: "#f9731615", padding: "2px 8px", borderRadius: 10 }}>{anomaliesElevees.length} élevée{anomaliesElevees.length > 1 ? "s" : ""}</span>}
                    {anomaliesMoyennes.length > 0 && <span style={{ fontSize: 10, color: "#eab308", background: "#eab30815", padding: "2px 8px", borderRadius: 10 }}>{anomaliesMoyennes.length} moyenne{anomaliesMoyennes.length > 1 ? "s" : ""}</span>}
                    {anomalesFaibles.length > 0 && <span style={{ fontSize: 10, color: "#22c55e", background: "#22c55e15", padding: "2px 8px", borderRadius: 10 }}>{anomalesFaibles.length} faible{anomalesFaibles.length > 1 ? "s" : ""}</span>}
                  </div>
                </div>
                {[...anomaliesCritiques, ...anomaliesElevees, ...anomaliesMoyennes, ...anomalesFaibles].map((a, i) => (
                  <AnomalyCard key={i} anomaly={a} index={i} />
                ))}
              </div>
            )}

            {result.anomalies?.length === 0 && (
              <div style={{
                background: "#22c55e08", border: "1px solid #22c55e22",
                borderRadius: 12, padding: 20, marginTop: 20, textAlign: "center",
                color: "#22c55e", fontSize: 13
              }}>
                ✅ Aucune anomalie détectée — Document conforme
              </div>
            )}

            {/* Re-analyze button */}
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <button
                onClick={() => { setResult(null); setFile(null); setError(null); }}
                style={{
                  background: "transparent", border: "1px solid #334155",
                  color: "#64748b", padding: "10px 24px", borderRadius: 8,
                  cursor: "pointer", fontSize: 12, letterSpacing: 1,
                  fontFamily: "'DM Mono', monospace", transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.target.style.borderColor = "#3b82f6"; e.target.style.color = "#3b82f6"; }}
                onMouseLeave={e => { e.target.style.borderColor = "#334155"; e.target.style.color = "#64748b"; }}
              >
                ↺ ANALYSER UN AUTRE DOCUMENT
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
