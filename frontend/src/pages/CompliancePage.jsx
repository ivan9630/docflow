import React, { useState, useEffect } from 'react'
import { listAnomalies, listFraudulent, resolveAnomaly, checkInterDocs, refreshCompliance } from '../api'
import { Panel, Table, Tr, Td, Spinner, Empty, Btn, SeverityBadge, TypeBadge } from '../components/UI'
import toast from 'react-hot-toast'

export default function CompliancePage() {
  const [anomalies, setAnomalies] = useState([])
  const [fraudDocs, setFraudDocs]  = useState([])
  const [tab, setTab]              = useState('anomalies')
  const [loading, setLoading]      = useState(true)
  const [sevFilter, setSevFilter]  = useState('')
  const [resolvedCount, setResolved] = useState(0)

  const load = async () => {
    setLoading(true)
    try {
      const [r1, r2] = await Promise.all([listAnomalies({ resolved: false }), listFraudulent()])
      setAnomalies(r1.data); setFraudDocs(r2.data)
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

  const filtered = sevFilter ? anomalies.filter(a => a.severite === sevFilter) : anomalies
  const crit = anomalies.filter(a => a.severite === 'critique').length
  const high = anomalies.filter(a => a.severite === 'elevee').length

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
          <Btn variant="ghost" size="sm" onClick={handleInterDocs}>🔗 Vérif. inter-docs</Btn>
          <Btn variant="ghost" size="sm" onClick={async () => { await refreshCompliance(); toast.success('Scores mis à jour'); load() }}>↺ Refresh scores</Btn>
        </div>
      </div>

      <div className="px-8 space-y-4">
        {/* Alertes critiques */}
        {crit > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl"
               style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid var(--danger)' }}>
            <span className="text-xl">🚨</span>
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
          {[['anomalies','Anomalies'],['fraude','Fraude radar']].map(([k,l]) => (
            <button key={k} onClick={() => setTab(k)}
              className="px-4 py-2 rounded-md text-sm font-medium transition-all"
              style={{ background: tab===k ? 'var(--accent)' : 'transparent', color: tab===k ? 'white' : 'var(--text2)' }}>
              {l}
            </button>
          ))}
        </div>

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

        {tab === 'fraude' && (
          <Panel title="Radar de fraude — Documents suspects">
            {fraudDocs.length === 0 ? <Empty icon="🛡️" title="Aucun document frauduleux" /> : (
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
