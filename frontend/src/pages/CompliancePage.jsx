import React, { useState, useEffect } from 'react'
import { listAnomalies, listFraudulent, listDocuments, getDocument, resolveAnomaly, checkInterDocs, refreshCompliance } from '../api'
import { Panel, Spinner, Empty, Btn, SeverityBadge, TypeBadge, KpiCard } from '../components/UI'
import { Check, X, Minus, Printer } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import toast from 'react-hot-toast'

const SEV_COLORS = { critique: '#e03131', elevee: '#e67700', moyenne: '#e8a500', faible: '#5c7cfa' }

function AutoField({ label, value, delay, accent }) {
  const [visible, setVisible] = useState(false)
  const [typed, setTyped] = useState('')
  const display = value ?? '—'
  useEffect(() => { setVisible(false); setTyped(''); const t = setTimeout(() => setVisible(true), delay); return () => clearTimeout(t) }, [value, delay])
  useEffect(() => { if (!visible || !display) return; let i = 0; setTyped(''); const iv = setInterval(() => { i++; setTyped(display.slice(0, i)); if (i >= display.length) clearInterval(iv) }, 18); return () => clearInterval(iv) }, [visible, display])
  return (
    <div>
      <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="rounded-lg px-3 py-2 text-sm transition-all duration-300"
           style={{ background: visible ? 'var(--surface2)' : 'var(--bg)', border: `1px solid ${visible ? 'var(--accent)' : 'var(--border)'}`, color: accent && visible ? 'var(--accent)' : 'var(--text)', fontWeight: accent ? 600 : 400 }}>
        {visible ? (typed || '\u00A0') : <span style={{ color: 'var(--text2)' }}>...</span>}
      </div>
    </div>
  )
}

function AnimatedGauge({ value, delay, danger }) {
  const [width, setWidth] = useState(0)
  useEffect(() => { setWidth(0); const t = setTimeout(() => setWidth(value ?? 0), delay); return () => clearTimeout(t) }, [value, delay])
  const color = danger ? (width > 70 ? 'var(--danger)' : width > 40 ? 'var(--warn)' : 'var(--accent2)') : (width > 80 ? 'var(--accent2)' : width > 50 ? 'var(--warn)' : 'var(--danger)')
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
        <div className="h-full rounded-full transition-all duration-1000 ease-out" style={{ width: `${width}%`, background: color }} />
      </div>
      <span className="text-sm font-bold w-10 text-right" style={{ color }}>{width}%</span>
    </div>
  )
}

function AutoCheck({ label, ok, delay, available }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => { setVisible(false); const t = setTimeout(() => setVisible(true), delay); return () => clearTimeout(t) }, [ok, delay])
  const notAvail = available === false
  return (
    <div className="flex items-center gap-2 text-sm transition-all duration-300" style={{ opacity: visible ? 1 : 0.3 }}>
      {visible ? (notAvail ? <Minus size={14} style={{ color: 'var(--text2)' }} /> : ok ? <Check size={14} style={{ color: 'var(--accent2)' }} /> : <X size={14} style={{ color: 'var(--danger)' }} />) : <span className="w-3.5 h-3.5 rounded-full border" style={{ borderColor: 'var(--border)' }} />}
      <span style={{ color: notAvail && visible ? 'var(--text2)' : 'var(--text)' }}>{label}{notAvail && visible ? ' (non detecte)' : ''}</span>
    </div>
  )
}

function exportReport(ficheData, anomaliesDoc) {
  const w = window.open('', '_blank')
  const fraudScore = ficheData?.score_fraude != null ? Math.round(ficheData.score_fraude * 100) : 0
  const verdict = ficheData.est_frauduleux ? 'SUSPECT' : anomaliesDoc.length > 0 ? 'ANOMALIES DETECTEES' : 'CONFORME'
  w.document.write(`<!DOCTYPE html><html><head><title>Rapport ${ficheData.nom_fichier}</title>
    <style>body{font-family:Arial,sans-serif;padding:40px;color:#1c1c28}h1{font-size:20px;margin-bottom:4px}h2{font-size:14px;color:#3b5bdb;margin-top:24px;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #e2e4ea;padding-bottom:4px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.field{margin-bottom:8px}.label{font-size:11px;color:#6b7084;text-transform:uppercase}.val{font-size:14px;font-weight:600}.verdict{padding:16px;border-radius:8px;text-align:center;font-weight:bold;font-size:16px;margin-top:20px}.anom{padding:8px;border-left:3px solid #e03131;margin:6px 0;background:#fef2f2}</style>
  </head><body>
    <h1>Rapport de conformite — DocuFlow</h1>
    <p style="color:#6b7084;font-size:13px">Document: ${ficheData.nom_fichier} &bull; Date: ${new Date().toLocaleDateString('fr-FR')}</p>
    <h2>Identification</h2>
    <div class="grid">
      <div class="field"><div class="label">Type</div><div class="val">${ficheData.type_document?.replace('DocumentType.', '') || '—'}</div></div>
      <div class="field"><div class="label">N document</div><div class="val">${ficheData.numero_document || '—'}</div></div>
      <div class="field"><div class="label">Date</div><div class="val">${ficheData.date_document || '—'}</div></div>
      <div class="field"><div class="label">OCR</div><div class="val">${ficheData.methode_ocr || '—'} (${((ficheData.score_ocr || 0) * 100).toFixed(0)}%)</div></div>
    </div>
    <h2>Fournisseur</h2>
    <div class="grid">
      <div class="field"><div class="label">Raison sociale</div><div class="val">${ficheData.nom_fournisseur || '—'}</div></div>
      <div class="field"><div class="label">SIREN</div><div class="val">${ficheData.numero_siren || '—'}</div></div>
      <div class="field"><div class="label">SIRET</div><div class="val">${ficheData.numero_siret || '—'}</div></div>
      <div class="field"><div class="label">TVA</div><div class="val">${ficheData.numero_tva || '—'}</div></div>
      <div class="field"><div class="label">IBAN</div><div class="val">${ficheData.iban || '—'}</div></div>
    </div>
    <h2>Montants</h2>
    <div class="grid">
      <div class="field"><div class="label">HT</div><div class="val">${ficheData.montant_ht ?? '—'} EUR</div></div>
      <div class="field"><div class="label">TVA</div><div class="val">${ficheData.montant_tva_val ?? '—'} EUR (${ficheData.taux_tva ?? '?'}%)</div></div>
      <div class="field"><div class="label">TTC</div><div class="val">${ficheData.montant_ttc ?? '—'} EUR</div></div>
    </div>
    <h2>Analyse</h2>
    <div class="field"><div class="label">Score de fraude</div><div class="val">${fraudScore}%</div></div>
    ${anomaliesDoc.length > 0 ? '<h2>Anomalies</h2>' + anomaliesDoc.map(a => `<div class="anom"><strong>${a.type || ''}</strong><br/>${a.description || ''}${a.valeur_trouvee ? `<br/>Trouve: ${a.valeur_trouvee}` : ''}${a.valeur_attendue ? ` | Attendu: ${a.valeur_attendue}` : ''}</div>`).join('') : ''}
    <div class="verdict" style="background:${ficheData.est_frauduleux ? '#fef2f2;color:#e03131;border:1px solid #e03131' : anomaliesDoc.length > 0 ? '#fff8e1;color:#e67700;border:1px solid #e67700' : '#e6fcf5;color:#0ca678;border:1px solid #0ca678'}">${verdict}</div>
    <p style="text-align:center;color:#6b7084;font-size:11px;margin-top:20px">Genere par DocuFlow v2 — ${new Date().toLocaleString('fr-FR')}</p>
  </body></html>`)
  w.document.close()
  w.print()
}

export default function CompliancePage() {
  const [anomalies, setAnomalies] = useState([])
  const [resolvedAnomalies, setResolvedAnomalies] = useState([])
  const [fraudDocs, setFraudDocs] = useState([])
  const [tab, setTab] = useState('fiche')
  const [loading, setLoading] = useState(true)
  const [sevFilter, setSevFilter] = useState('')
  const [recentDocs, setRecentDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [ficheData, setFicheData] = useState(null)
  const [ficheLoading, setFicheLoading] = useState(false)
  const [filling, setFilling] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [r1, r2, r3, r4] = await Promise.all([
        listAnomalies({ resolved: false }), listFraudulent(), listDocuments({ limit: 20 }),
        listAnomalies({ resolved: true })
      ])
      setAnomalies(r1.data); setFraudDocs(r2.data); setResolvedAnomalies(r4.data)
      setRecentDocs((r3.data.documents || []).filter(d => !['DocumentStatus.UPLOADE','DocumentStatus.EN_TRAITEMENT'].includes(d.statut)))
    } catch { toast.error('Erreur chargement') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleResolve = async (id) => {
    try {
      await resolveAnomaly(id, 'Resolu manuellement')
      setAnomalies(p => p.filter(a => a.id !== id))
      load()
      toast.success('Anomalie resolue')
    } catch { toast.error('Erreur') }
  }

  const loadFiche = async (docId) => {
    setSelectedDoc(docId); setFicheData(null); setFilling(false); setFicheLoading(true)
    try { const r = await getDocument(docId); setFicheData(r.data); setTimeout(() => setFilling(true), 300) }
    catch { toast.error('Erreur chargement') }
    finally { setFicheLoading(false) }
  }

  const filtered = sevFilter ? anomalies.filter(a => a.severite === sevFilter) : anomalies
  const crit = anomalies.filter(a => a.severite === 'critique').length
  const high = anomalies.filter(a => a.severite === 'elevee').length
  const fraudScore = ficheData?.score_fraude != null ? Math.round(ficheData.score_fraude * 100) : 0
  const anomaliesDoc = ficheData?.anomalies || []

  // Chart data
  const sevData = ['critique', 'elevee', 'moyenne', 'faible'].map(s => ({ name: s, value: anomalies.filter(a => a.severite === s).length })).filter(d => d.value > 0)
  const typeCount = {}
  anomalies.forEach(a => { const t = a.type?.replace(/_/g, ' ') || '?'; typeCount[t] = (typeCount[t] || 0) + 1 })
  const typeData = Object.entries(typeCount).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, value]) => ({ name, value }))

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold">Outil de Conformite</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>Detection fraude et incoherences — {anomalies.length} anomalie(s)</p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={async () => { const r = await checkInterDocs(); toast.success(`${r.data.new_anomalies} anomalie(s) inter-docs`); load() }}>Verif. inter-docs</Btn>
          <Btn variant="ghost" size="sm" onClick={async () => { await refreshCompliance(); toast.success('Scores mis a jour'); load() }}>Refresh</Btn>
        </div>
      </div>

      <div className="px-8 space-y-4">
        {/* KPIs */}
        <div className="grid grid-cols-4 gap-3">
          <KpiCard label="Critiques" value={crit} color="danger" />
          <KpiCard label="Elevees" value={high} color="warning" />
          <KpiCard label="Frauduleux" value={fraudDocs.length} color="gold" />
          <KpiCard label="Resolues" value={resolvedAnomalies.length} color="success" />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ background: 'var(--surface2)' }}>
          {[['fiche','Fiche controle'],['anomalies','Anomalies'],['fraude','Fraude'],['historique','Historique']].map(([k,l]) => (
            <button key={k} onClick={() => setTab(k)}
              className="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
              style={{ background: tab===k ? 'var(--surface)' : 'transparent', color: tab===k ? 'var(--text)' : 'var(--text2)', boxShadow: tab===k ? '0 1px 3px rgba(0,0,0,0.08)' : 'none' }}>
              {l}
            </button>
          ))}
        </div>

        {/* FICHE */}
        {tab === 'fiche' && (
          <div className="grid grid-cols-3 gap-4">
            <Panel title="Documents traites">
              {loading ? <Spinner /> : recentDocs.length === 0 ? <Empty title="Aucun document" /> : (
                <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                  {recentDocs.map(d => (
                    <div key={d.id} onClick={() => loadFiche(d.id)}
                         className="flex items-center gap-3 px-4 py-3 cursor-pointer transition-all hover:bg-gray-50"
                         style={{ borderLeft: selectedDoc === d.id ? '3px solid var(--accent)' : '3px solid transparent' }}>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{d.nom_fichier}</div>
                        <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>{d.type_document?.replace('DocumentType.', '') || '—'} &middot; {d.nom_fournisseur || '—'}</div>
                      </div>
                      {d.est_frauduleux && <span className="text-xs font-semibold px-1.5 py-0.5 rounded" style={{ background: 'rgba(224,49,49,0.08)', color: 'var(--danger)' }}>Suspect</span>}
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <div className="col-span-2 space-y-4">
              {ficheLoading && <Spinner />}
              {!ficheData && !ficheLoading && <Panel><Empty title="Selectionnez un document" sub="Cliquez a gauche pour voir la fiche" /></Panel>}
              {ficheData && filling && (
                <>
                  <Panel title="Fiche de controle" action={
                    <button onClick={() => exportReport(ficheData, anomaliesDoc)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-gray-100 transition-all" style={{ border: '1px solid var(--border)', color: 'var(--text2)' }}>
                      <Printer size={13} /> Exporter
                    </button>
                  }>
                    <div className="p-5 space-y-5">
                      <div>
                        <div className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--accent)' }}>Identification</div>
                        <div className="grid grid-cols-2 gap-3">
                          <AutoField label="Fichier" value={ficheData.nom_fichier} delay={100} />
                          <AutoField label="Type" value={ficheData.type_document?.replace('DocumentType.', '')?.toUpperCase()} delay={250} accent />
                          <AutoField label="N document" value={ficheData.numero_document || 'Non detecte'} delay={400} />
                          <AutoField label="Date" value={ficheData.date_document || 'Non detectee'} delay={550} />
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--accent)' }}>Fournisseur</div>
                        <div className="grid grid-cols-2 gap-3">
                          <AutoField label="Raison sociale" value={ficheData.nom_fournisseur || 'Non detecte'} delay={700} />
                          <AutoField label="SIREN" value={ficheData.numero_siren || 'Non detecte'} delay={850} />
                          <AutoField label="SIRET" value={ficheData.numero_siret || 'Non detecte'} delay={1000} />
                          <AutoField label="N TVA" value={ficheData.numero_tva || 'Non detecte'} delay={1150} />
                          <AutoField label="IBAN" value={ficheData.iban || 'Non detecte'} delay={1300} />
                          <AutoField label="Expiration" value={ficheData.date_expiration || 'N/A'} delay={1450} />
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold mb-2 uppercase tracking-wide" style={{ color: 'var(--accent)' }}>Montants</div>
                        <div className="grid grid-cols-3 gap-3">
                          <AutoField label="HT" value={ficheData.montant_ht != null ? `${ficheData.montant_ht} EUR` : 'N/A'} delay={1600} />
                          <AutoField label="TVA" value={ficheData.montant_tva_val != null ? `${ficheData.montant_tva_val} EUR (${ficheData.taux_tva || '?'}%)` : 'N/A'} delay={1750} />
                          <AutoField label="TTC" value={ficheData.montant_ttc != null ? `${ficheData.montant_ttc} EUR` : 'N/A'} delay={1900} accent />
                        </div>
                      </div>
                    </div>
                  </Panel>

                  <Panel title="Analyse de conformite">
                    <div className="p-5 space-y-5">
                      <div>
                        <div className="text-xs font-semibold mb-2">Score de fraude</div>
                        <AnimatedGauge value={fraudScore} delay={2100} danger />
                      </div>
                      <div>
                        <div className="text-xs font-semibold mb-2">Verifications automatiques</div>
                        <div className="space-y-1.5">
                          <AutoCheck label="SIRET coherent avec SIREN" ok={!anomaliesDoc.some(a => a.type?.includes('siret'))} delay={2300} available={!!(ficheData.numero_siret && ficheData.numero_siren)} />
                          <AutoCheck label="N TVA valide" ok={!anomaliesDoc.some(a => a.type?.includes('tva'))} delay={2500} available={!!ficheData.numero_tva} />
                          <AutoCheck label="Montants HT/TVA/TTC coherents" ok={!anomaliesDoc.some(a => a.type?.includes('montant'))} delay={2700} available={!!(ficheData.montant_ht && ficheData.montant_ttc)} />
                          <AutoCheck label="IBAN conforme" ok={!anomaliesDoc.some(a => a.type?.includes('iban'))} delay={2900} available={!!ficheData.iban} />
                          <AutoCheck label="Document non expire" ok={!anomaliesDoc.some(a => a.type?.includes('expir'))} delay={3100} available={!!ficheData.date_expiration} />
                        </div>
                      </div>
                      <div className="rounded-lg p-4 text-center" style={{
                        background: ficheData.est_frauduleux ? 'rgba(224,49,49,0.06)' : anomaliesDoc.length > 0 ? 'rgba(230,119,0,0.06)' : 'rgba(12,166,120,0.06)',
                        border: `1px solid ${ficheData.est_frauduleux ? 'var(--danger)' : anomaliesDoc.length > 0 ? 'var(--warn)' : 'var(--accent2)'}`
                      }}>
                        <div className="font-bold" style={{ color: ficheData.est_frauduleux ? 'var(--danger)' : anomaliesDoc.length > 0 ? 'var(--warn)' : 'var(--accent2)' }}>
                          {ficheData.est_frauduleux ? 'Document suspect — Verification requise' : anomaliesDoc.length > 0 ? 'Anomalies detectees — Revue recommandee' : 'Document conforme'}
                        </div>
                      </div>
                    </div>
                  </Panel>
                </>
              )}
            </div>
          </div>
        )}

        {/* ANOMALIES */}
        {tab === 'anomalies' && (
          <div className="space-y-4">
            {/* Charts */}
            {anomalies.length > 0 && (
              <div className="grid grid-cols-2 gap-4">
                <Panel title="Repartition par severite">
                  <div className="p-4 flex justify-center">
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={sevData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={11}>
                          {sevData.map(d => <Cell key={d.name} fill={SEV_COLORS[d.name] || '#6b7084'} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </Panel>
                <Panel title="Repartition par type">
                  <div className="p-4">
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={typeData} layout="vertical" margin={{ left: 100 }}>
                        <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7084' }} />
                        <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#6b7084' }} width={100} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#e67700" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Panel>
              </div>
            )}

            <Panel title="Anomalies ouvertes" action={
              <select className="text-xs rounded px-2 py-1" style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }}
                      value={sevFilter} onChange={e => setSevFilter(e.target.value)}>
                {[['','Toutes'],['critique','Critique'],['elevee','Elevee'],['moyenne','Moyenne']].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            }>
              {loading ? <Spinner /> : filtered.length === 0 ? <Empty title="Aucune anomalie" sub="Tout est conforme" /> : (
                <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                  {filtered.map(a => (
                    <div key={a.id} className="flex items-start gap-4 px-5 py-4">
                      <div className="w-1 self-stretch rounded-full flex-shrink-0" style={{ background: SEV_COLORS[a.severite] || '#6b7084' }} />
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium uppercase" style={{ color: 'var(--text2)' }}>{a.type?.replace(/_/g,' ')}</div>
                        <div className="text-sm font-medium mt-0.5">{a.description}</div>
                        {(a.valeur_trouvee || a.valeur_attendue) && (
                          <div className="flex gap-4 mt-1 text-xs">
                            {a.valeur_trouvee && <span style={{ color: 'var(--danger)' }}>Trouve: {a.valeur_trouvee}</span>}
                            {a.valeur_attendue && <span style={{ color: 'var(--accent2)' }}>Attendu: {a.valeur_attendue}</span>}
                          </div>
                        )}
                      </div>
                      <SeverityBadge sev={a.severite} />
                      <Btn variant="ghost" size="sm" onClick={() => handleResolve(a.id)}>Resoudre</Btn>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>
        )}

        {/* FRAUDE */}
        {tab === 'fraude' && (
          <Panel title="Documents suspects">
            {fraudDocs.length === 0 ? <Empty title="Aucun document frauduleux" /> : (
              <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {fraudDocs.map(d => {
                  const pct = Math.round((d.score || 0) * 100)
                  return (
                    <div key={d.id} className="flex items-center gap-4 px-5 py-4">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                           style={{ border: '2px solid var(--danger)', color: 'var(--danger)' }}>{pct}%</div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{d.nom}</div>
                        <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>{d.fournisseur || '—'} &middot; <TypeBadge type={d.type} /></div>
                        {d.anomalies?.length > 0 && (
                          <div className="text-xs mt-1" style={{ color: 'var(--warn)' }}>{d.anomalies.length} anomalie(s) : {d.anomalies.slice(0, 3).map(a => a.type?.replace(/_/g, ' ')).join(', ')}</div>
                        )}
                      </div>
                      <span className="text-xs font-semibold px-2 py-1 rounded" style={{ background: 'rgba(224,49,49,0.08)', color: 'var(--danger)' }}>Suspect</span>
                    </div>
                  )
                })}
              </div>
            )}
          </Panel>
        )}

        {/* HISTORIQUE */}
        {tab === 'historique' && (
          <Panel title={`Historique des resolutions (${resolvedAnomalies.length})`}>
            {resolvedAnomalies.length === 0 ? <Empty title="Aucune resolution" sub="Les anomalies resolues apparaitront ici" /> : (
              <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {resolvedAnomalies.map(a => (
                  <div key={a.id} className="flex items-start gap-4 px-5 py-3">
                    <div className="mt-1 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(12,166,120,0.1)' }}>
                      <Check size={12} style={{ color: 'var(--accent2)' }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{a.description}</div>
                      <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>
                        {a.type?.replace(/_/g, ' ')} &middot; {a.created_at ? new Date(a.created_at).toLocaleDateString('fr-FR') : ''}
                      </div>
                    </div>
                    <SeverityBadge sev={a.severite} />
                  </div>
                ))}
              </div>
            )}
          </Panel>
        )}
      </div>
    </div>
  )
}
