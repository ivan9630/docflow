import React, { useState, useEffect, useRef } from 'react'
import { listAnomalies, listFraudulent, listDocuments, getDocument, resolveAnomaly, checkInterDocs, refreshCompliance } from '../api'
import { Panel, Table, Tr, Td, Spinner, Empty, Btn, SeverityBadge, TypeBadge } from '../components/UI'
import toast from 'react-hot-toast'

/* ── Champ auto-rempli avec animation ─────────────────────────── */
function AutoField({ label, value, delay, color }) {
  const [visible, setVisible] = useState(false)
  const [typed, setTyped] = useState('')
  const display = value ?? '—'

  useEffect(() => {
    setVisible(false)
    setTyped('')
    const showTimer = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(showTimer)
  }, [value, delay])

  useEffect(() => {
    if (!visible || !display) return
    let i = 0
    setTyped('')
    const interval = setInterval(() => {
      i++
      setTyped(display.slice(0, i))
      if (i >= display.length) clearInterval(interval)
    }, 18)
    return () => clearInterval(interval)
  }, [visible, display])

  return (
    <div className="space-y-1">
      <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="rounded-lg px-3 py-2 text-sm min-h-[36px] transition-all duration-300"
           style={{
             background: visible ? 'var(--surface2)' : 'var(--surface)',
             border: `1px solid ${visible ? (color || 'var(--accent)') + '66' : 'var(--border)'}`,
             color: color || 'var(--text)',
           }}>
        {visible ? (typed || '\u00A0') : <span style={{ color: 'var(--text2)' }}>...</span>}
      </div>
    </div>
  )
}

/* ── Jauge animée ─────────────────────────────────────────────── */
function AnimatedGauge({ value, delay, danger }) {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    setWidth(0)
    const t = setTimeout(() => setWidth(value ?? 0), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  const color = danger
    ? (width > 70 ? 'var(--danger)' : width > 40 ? 'var(--warn)' : 'var(--accent2)')
    : (width > 80 ? 'var(--accent2)' : width > 50 ? 'var(--warn)' : 'var(--danger)')
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
        <div className="h-full rounded-full transition-all duration-1000 ease-out" style={{ width: `${width}%`, background: color }} />
      </div>
      <span className="font-mono text-sm font-bold" style={{ color }}>{width}%</span>
    </div>
  )
}

/* ── Check animé ──────────────────────────────────────────────── */
function AutoCheck({ label, ok, delay, available }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    setVisible(false)
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [ok, delay])

  const notAvailable = available === false
  return (
    <div className="flex items-center gap-2 text-sm transition-all duration-300" style={{ opacity: visible ? 1 : 0.3 }}>
      <span style={{ color: visible ? (notAvailable ? 'var(--text2)' : ok ? 'var(--accent2)' : 'var(--danger)') : 'var(--text2)' }}>
        {visible ? (notAvailable ? '—' : ok ? '✓' : '✗') : '○'}
      </span>
      <span style={{ color: notAvailable && visible ? 'var(--text2)' : undefined }}>
        {label}{notAvailable && visible ? ' (non détecté)' : ''}
      </span>
    </div>
  )
}

export default function CompliancePage() {
  const [anomalies, setAnomalies] = useState([])
  const [fraudDocs, setFraudDocs]  = useState([])
  const [tab, setTab]              = useState('fiche')
  const [loading, setLoading]      = useState(true)
  const [sevFilter, setSevFilter]  = useState('')
  const [resolvedCount, setResolved] = useState(0)

  // Fiche contrôle auto-remplie
  const [recentDocs, setRecentDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [ficheData, setFicheData] = useState(null)
  const [ficheLoading, setFicheLoading] = useState(false)
  const [filling, setFilling] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [r1, r2, r3] = await Promise.all([
        listAnomalies({ resolved: false }),
        listFraudulent(),
        listDocuments({ limit: 20 })
      ])
      setAnomalies(r1.data); setFraudDocs(r2.data)
      const docs = r3.data.documents?.filter(d => d.statut !== 'DocumentStatus.UPLOADE' && d.statut !== 'DocumentStatus.EN_TRAITEMENT') || []
      setRecentDocs(docs)
    } catch { toast.error('Erreur chargement') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleResolve = async (id) => {
    try {
      await resolveAnomaly(id, 'Résolu manuellement')
      setAnomalies(p => p.filter(a => a.id !== id))
      setResolved(p => p + 1)
      toast.success('Anomalie résolue')
    } catch { toast.error('Erreur') }
  }

  const handleInterDocs = async () => {
    try {
      const r = await checkInterDocs()
      toast.success(`${r.data.new_anomalies} nouvelle(s) anomalie(s) inter-documents détectée(s)`)
      load()
    } catch { toast.error('Erreur') }
  }

  /* ── Charger la fiche contrôle d'un document ── */
  const loadFiche = async (docId) => {
    setSelectedDoc(docId)
    setFicheData(null)
    setFilling(false)
    setFicheLoading(true)
    try {
      const r = await getDocument(docId)
      setFicheData(r.data)
      // Déclencher l'animation de remplissage
      setTimeout(() => setFilling(true), 300)
    } catch { toast.error('Erreur chargement document') }
    finally { setFicheLoading(false) }
  }

  const filtered = sevFilter ? anomalies.filter(a => a.severite === sevFilter) : anomalies
  const crit = anomalies.filter(a => a.severite === 'critique').length
  const high = anomalies.filter(a => a.severite === 'elevee').length

  const fraudScore = ficheData?.score_fraude != null ? Math.round(ficheData.score_fraude * 100) : 0
  const anomaliesDoc = ficheData?.anomalies || []

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Outil de Conformité</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
            Détection fraude & incohérences — {anomalies.length} anomalie(s) ouverte(s)
          </p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={handleInterDocs}>Vérif. inter-docs</Btn>
          <Btn variant="ghost" size="sm" onClick={async () => { await refreshCompliance(); toast.success('Scores mis à jour'); load() }}>Refresh scores</Btn>
        </div>
      </div>

      <div className="px-8 space-y-4">
        {/* Alertes critiques */}
        {crit > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl"
               style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid var(--danger)' }}>
            <span className="font-medium" style={{ color: 'var(--danger)' }}>
              {crit} anomalie(s) CRITIQUE(S) et {high} élevée(s) nécessitent une intervention immédiate
            </span>
          </div>
        )}

        {/* KPIs */}
        <div className="grid grid-cols-4 gap-4">
          {[
            ['Critiques',      crit,              'var(--danger)'],
            ['Élevées',        high,              'var(--warn)'],
            ['Frauduleux',     fraudDocs.length,  'var(--gold)'],
            ['Résolues',       resolvedCount,     'var(--accent2)'],
          ].map(([l,v,c]) => (
            <div key={l} className="rounded-xl p-4" style={{ background: 'var(--surface)', border: `1px solid ${c}33` }}>
              <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>{l}</div>
              <div className="font-display text-3xl font-bold mt-1" style={{ color: c }}>{v}</div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ background: 'var(--surface2)' }}>
          {[['fiche','Fiche contrôle'],['anomalies','Anomalies'],['fraude','Fraude radar']].map(([k,l]) => (
            <button key={k} onClick={() => setTab(k)}
              className="px-4 py-2 rounded-md text-sm font-medium transition-all"
              style={{ background: tab===k ? 'var(--accent)' : 'transparent', color: tab===k ? 'white' : 'var(--text2)' }}>
              {l}
            </button>
          ))}
        </div>

        {/* ── FICHE CONTRÔLE AUTO-REMPLIE ── */}
        {tab === 'fiche' && (
          <div className="grid grid-cols-3 gap-4">
            {/* Liste documents à contrôler */}
            <Panel title="Documents traités">
              {loading ? <Spinner /> : recentDocs.length === 0 ? <Empty title="Aucun document" sub="Uploadez un document pour commencer" /> : (
                <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                  {recentDocs.map(d => (
                    <div key={d.id}
                         className="flex items-center gap-3 px-4 py-3 cursor-pointer transition-all hover:opacity-80"
                         style={{
                           background: selectedDoc === d.id ? 'var(--accent)11' : 'transparent',
                           borderLeft: selectedDoc === d.id ? '3px solid var(--accent)' : '3px solid transparent'
                         }}
                         onClick={() => loadFiche(d.id)}>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{d.nom_fichier}</div>
                        <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>
                          {d.type_document?.replace('DocumentType.', '') || '—'} · {d.nom_fournisseur || '—'}
                        </div>
                      </div>
                      {d.est_frauduleux && <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,51,102,0.15)', color: 'var(--danger)' }}>SUSPECT</span>}
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            {/* Formulaire auto-rempli */}
            <div className="col-span-2 space-y-4">
              {ficheLoading && <Spinner />}
              {!ficheData && !ficheLoading && (
                <Panel>
                  <Empty title="Sélectionnez un document" sub="Cliquez sur un document à gauche pour voir sa fiche de contrôle auto-remplie" />
                </Panel>
              )}
              {ficheData && filling && (
                <>
                  {/* En-tête fiche */}
                  <Panel title="Fiche de contrôle — Auto-remplie par l'IA">
                    <div className="p-5 space-y-5">
                      {/* Identification */}
                      <div>
                        <div className="font-display font-bold text-sm mb-3" style={{ color: 'var(--accent)' }}>Identification du document</div>
                        <div className="grid grid-cols-2 gap-3">
                          <AutoField label="Fichier" value={ficheData.nom_fichier} delay={100} />
                          <AutoField label="Type classifié" value={ficheData.type_document?.replace('DocumentType.', '')?.toUpperCase()} delay={250} color="var(--accent)" />
                          <AutoField label="Numéro document" value={ficheData.numero_document || 'Non détecté'} delay={400} />
                          <AutoField label="Date document" value={ficheData.date_document || 'Non détectée'} delay={550} />
                        </div>
                      </div>

                      {/* Fournisseur */}
                      <div>
                        <div className="font-display font-bold text-sm mb-3" style={{ color: 'var(--accent)' }}>Fournisseur</div>
                        <div className="grid grid-cols-2 gap-3">
                          <AutoField label="Raison sociale" value={ficheData.nom_fournisseur || 'Non détecté'} delay={700} />
                          <AutoField label="SIREN" value={ficheData.numero_siren || 'Non détecté'} delay={850} />
                          <AutoField label="SIRET" value={ficheData.numero_siret || 'Non détecté'} delay={1000} />
                          <AutoField label="N° TVA" value={ficheData.numero_tva || 'Non détecté'} delay={1150} />
                          <AutoField label="IBAN" value={ficheData.iban || 'Non détecté'} delay={1300} />
                          <AutoField label="Date expiration" value={ficheData.date_expiration || 'N/A'} delay={1450} />
                        </div>
                      </div>

                      {/* Montants */}
                      <div>
                        <div className="font-display font-bold text-sm mb-3" style={{ color: 'var(--accent)' }}>Montants</div>
                        <div className="grid grid-cols-3 gap-3">
                          <AutoField label="Montant HT" value={ficheData.montant_ht != null ? `${ficheData.montant_ht} €` : 'N/A'} delay={1600} />
                          <AutoField label="TVA" value={ficheData.montant_tva_val != null ? `${ficheData.montant_tva_val} € (${ficheData.taux_tva || '?'}%)` : 'N/A'} delay={1750} />
                          <AutoField label="Montant TTC" value={ficheData.montant_ttc != null ? `${ficheData.montant_ttc} €` : 'N/A'} delay={1900} color="var(--accent)" />
                        </div>
                      </div>
                    </div>
                  </Panel>

                  {/* Score fraude + vérifications */}
                  <Panel title="Analyse de conformité">
                    <div className="p-5 space-y-5">
                      {/* Score fraude */}
                      <div>
                        <div className="font-display font-bold text-sm mb-3">Score de fraude</div>
                        <AnimatedGauge value={fraudScore} delay={2100} danger />
                      </div>

                      {/* Vérifications */}
                      <div>
                        <div className="font-display font-bold text-sm mb-3">Vérifications automatiques</div>
                        <div className="space-y-2">
                          <AutoCheck label="SIRET cohérent avec SIREN" ok={!anomaliesDoc.some(a => a.type?.includes('siret'))} delay={2300} available={!!(ficheData.numero_siret && ficheData.numero_siren)} />
                          <AutoCheck label="N° TVA valide" ok={!anomaliesDoc.some(a => a.type?.includes('tva'))} delay={2500} available={!!ficheData.numero_tva} />
                          <AutoCheck label="Montants HT/TVA/TTC cohérents" ok={!anomaliesDoc.some(a => a.type?.includes('montant'))} delay={2700} available={!!(ficheData.montant_ht && ficheData.montant_ttc)} />
                          <AutoCheck label="IBAN conforme" ok={!anomaliesDoc.some(a => a.type?.includes('iban'))} delay={2900} available={!!ficheData.iban} />
                          <AutoCheck label="Document non expiré" ok={!anomaliesDoc.some(a => a.type?.includes('expir'))} delay={3100} available={!!ficheData.date_expiration} />
                          <AutoCheck label="Type de document reconnu" ok={!anomaliesDoc.some(a => a.type?.includes('type_non_reconnu'))} delay={3300} available={true} />
                        </div>
                      </div>

                      {/* Anomalies détaillées */}
                      {anomaliesDoc.length > 0 && (
                        <div>
                          <div className="font-display font-bold text-sm mb-3" style={{ color: 'var(--danger)' }}>
                            Anomalies détectées ({anomaliesDoc.length})
                          </div>
                          <div className="space-y-2">
                            {anomaliesDoc.map((a, i) => (
                              <div key={i} className="flex items-start gap-3 rounded-lg p-3"
                                   style={{ background: 'rgba(255,51,102,0.06)', border: '1px solid var(--danger)', animationDelay: `${3400 + i * 200}ms` }}>
                                <div className="w-1.5 self-stretch rounded-full flex-shrink-0" style={{
                                  background: a.severite === 'critique' ? 'var(--danger)' : a.severite === 'elevee' ? 'var(--warn)' : 'var(--gold)'
                                }} />
                                <div>
                                  <div className="text-sm font-medium">{a.description || a.type}</div>
                                  {a.valeur_trouvee && (
                                    <div className="text-xs mt-1 font-mono">
                                      <span style={{ color: 'var(--danger)' }}>Trouvé: {a.valeur_trouvee}</span>
                                      {a.valeur_attendue && <span style={{ color: 'var(--accent2)' }}> | Attendu: {a.valeur_attendue}</span>}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Verdict */}
                      <div className="rounded-xl p-4 text-center" style={{
                        background: ficheData.est_frauduleux ? 'rgba(255,51,102,0.1)' : anomaliesDoc.length > 0 ? 'rgba(255,170,0,0.1)' : 'rgba(0,230,118,0.1)',
                        border: `1px solid ${ficheData.est_frauduleux ? 'var(--danger)' : anomaliesDoc.length > 0 ? 'var(--warn)' : 'var(--accent2)'}`
                      }}>
                        <div className="font-display font-bold text-lg" style={{
                          color: ficheData.est_frauduleux ? 'var(--danger)' : anomaliesDoc.length > 0 ? 'var(--warn)' : 'var(--accent2)'
                        }}>
                          {ficheData.est_frauduleux ? 'DOCUMENT SUSPECT — Vérification manuelle requise'
                            : anomaliesDoc.length > 0 ? 'ANOMALIES DÉTECTÉES — Revue recommandée'
                            : 'DOCUMENT CONFORME'}
                        </div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>
                          OCR: {ficheData.methode_ocr} (confiance {(ficheData.score_ocr * 100)?.toFixed(0)}%) · Classification: confiance {(ficheData.score_classification * 100)?.toFixed(0)}%
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-3 justify-end">
                        <Btn variant="ghost" onClick={() => { handleResolve(ficheData.id); toast.success('Document marqué conforme') }}>Marquer conforme</Btn>
                        <Btn variant="primary" onClick={() => { toast.success('Rapport exporté') }}>Exporter rapport</Btn>
                      </div>
                    </div>
                  </Panel>

                  {/* Pipeline */}
                  <Panel title="Pipeline de traitement">
                    <div className="p-5">
                      <div className="flex items-center gap-2">
                        {(ficheData.pipeline_steps || []).map((step, i) => (
                          <React.Fragment key={i}>
                            <div className="flex items-center gap-2 rounded-lg px-3 py-2"
                                 style={{ background: 'var(--surface2)', border: '1px solid var(--border)' }}>
                              <span style={{ color: 'var(--accent2)' }}>✓</span>
                              <div>
                                <div className="text-xs font-medium uppercase">{step.etape}</div>
                                <div className="text-xs font-mono" style={{ color: 'var(--text2)' }}>{step.ms}ms</div>
                              </div>
                            </div>
                            {i < (ficheData.pipeline_steps || []).length - 1 && (
                              <div style={{ color: 'var(--text2)' }}>→</div>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </Panel>
                </>
              )}
            </div>
          </div>
        )}

        {/* ── ANOMALIES ── */}
        {tab === 'anomalies' && (
          <Panel title="Anomalies ouvertes" action={
            <select className="text-xs rounded px-2 py-1"
                    style={{ background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                    value={sevFilter} onChange={e => setSevFilter(e.target.value)}>
              {[['','Toutes'],['critique','Critique'],['elevee','Élevée'],['moyenne','Moyenne'],['faible','Faible']].map(([v,l]) =>
                <option key={v} value={v}>{l}</option>)}
            </select>
          }>
            {loading ? <Spinner /> : filtered.length === 0 ? <Empty icon="✅" title="Aucune anomalie" sub="Tout est conforme !" /> : (
              <div className="divide-y" style={{ divideColor: 'var(--border)' }}>
                {filtered.map(a => (
                  <div key={a.id} className="flex items-start gap-4 px-5 py-4">
                    <div className="w-1.5 self-stretch rounded-full flex-shrink-0"
                         style={{ background: a.severite==='critique'?'var(--danger)':a.severite==='elevee'?'var(--warn)':a.severite==='moyenne'?'var(--gold)':'#6699ff' }} />
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>
                        {a.type?.replace(/_/g,' ')}
                      </div>
                      <div className="text-sm font-medium mt-0.5">{a.description}</div>
                      {(a.valeur_trouvee || a.valeur_attendue) && (
                        <div className="flex gap-4 mt-1">
                          {a.valeur_trouvee && <span className="font-mono text-xs" style={{ color: 'var(--danger)' }}>Trouvé: {a.valeur_trouvee}</span>}
                          {a.valeur_attendue && <span className="font-mono text-xs" style={{ color: 'var(--accent2)' }}>Attendu: {a.valeur_attendue}</span>}
                        </div>
                      )}
                      <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>
                        {new Date(a.created_at).toLocaleString('fr-FR')}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <SeverityBadge sev={a.severite} />
                      <Btn variant="ghost" size="sm" onClick={() => handleResolve(a.id)}>Résoudre</Btn>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        )}

        {/* ── FRAUDE RADAR ── */}
        {tab === 'fraude' && (
          <Panel title="Radar de fraude — Documents suspects">
            {fraudDocs.length === 0 ? <Empty title="Aucun document frauduleux" /> : (
              <div className="p-4 space-y-3">
                {fraudDocs.map(d => {
                  const pct = Math.round((d.score || 0) * 100)
                  return (
                    <div key={d.id} className="flex items-center gap-4 rounded-xl p-4"
                         style={{ background: 'rgba(255,51,102,0.08)', border: '1px solid var(--danger)' }}>
                      <div className="w-14 h-14 rounded-full flex items-center justify-center font-display font-bold text-lg flex-shrink-0"
                           style={{ border: `3px solid var(--danger)`, color: 'var(--danger)' }}>{pct}%</div>
                      <div className="flex-1">
                        <div className="font-medium">{d.nom}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>
                          {d.fournisseur || '—'} · <TypeBadge type={d.type} />
                        </div>
                        {d.anomalies?.length > 0 && (
                          <div className="text-xs mt-1" style={{ color: 'var(--warn)' }}>
                            {d.anomalies.length} anomalie(s) : {d.anomalies.slice(0,2).map(a => a.type).join(', ')}
                          </div>
                        )}
                      </div>
                      <span className="font-mono text-xs font-bold px-2 py-1 rounded"
                            style={{ background: 'rgba(255,51,102,0.15)', color: 'var(--danger)' }}>SUSPECT</span>
                    </div>
                  )
                })}
              </div>
            )}
          </Panel>
        )}
      </div>
    </div>
  )
}
