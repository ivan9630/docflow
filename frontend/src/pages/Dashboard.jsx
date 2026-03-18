import React, { useEffect, useState, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { RefreshCw, AlertTriangle, Upload, Loader } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { dashboardStats, autofillCRM, triggerDAG, uploadDocuments, getDocStatus, listDocuments, validateDoc, rejectDoc, reprocessDoc } from '../api'
import { KpiCard, Panel, Btn, Spinner, StatusPill, TypeBadge, ZoneBadge, FraudScore, Table, Tr, Td, Empty } from '../components/UI'
import toast from 'react-hot-toast'

const COLORS = ['#6c63ff','#00d4aa','#ff6b35','#ffd166','#ff3366','#8b85ff']
const STAGES = ['uploade','en_traitement','ocr_ok','extrait','verifie','valide']
const ZONE_PCT = { raw:20, clean:60, curated:95 }
const norm = (s) => s ? s.replace('DocumentStatus.','').replace('DataZone.','').toLowerCase() : ''

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('overview')

  // Upload
  const [queue, setQueue] = useState([])
  const [uploading, setUploading] = useState(false)

  // Documents
  const [docs, setDocs] = useState([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState({ status: '', type: '', q: '' })

  const loadStats = useCallback(async () => {
    try {
      const r = await dashboardStats()
      setStats(r.data)
    } catch {}
    finally { setLoading(false) }
  }, [])

  const loadDocs = async () => {
    setDocsLoading(true)
    try {
      const r = await listDocuments({ limit: 100 })
      setDocs(r.data.documents || [])
    } catch {}
    finally { setDocsLoading(false) }
  }

  useEffect(() => { loadStats(); loadDocs(); const i = setInterval(loadStats, 20000); return () => clearInterval(i) }, [loadStats])

  // Upload
  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return
    setUploading(true)
    setTab('upload')
    const form = new FormData()
    accepted.forEach(f => form.append('files', f))
    try {
      const r = await uploadDocuments(form)
      const results = r.data.results || []
      const newItems = results.map(res => ({
        id: res.doc_id, filename: res.filename,
        status: res.status === 'queued' ? 'en_traitement' : 'error',
        zone: 'raw', progress: 10, message: res.message,
      }))
      setQueue(prev => [...newItems, ...prev])
      toast.success(`${r.data.uploaded} fichier(s) en cours de traitement`)
    } catch (e) { toast.error('Erreur upload') }
    finally { setUploading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf':[], 'image/jpeg':[], 'image/png':[], 'image/tiff':[] },
    maxFiles: 20, maxSize: 50 * 1024 * 1024
  })

  // Polling upload
  useEffect(() => {
    const processing = queue.filter(q => !['valide','anomalie','rejete','error'].includes(norm(q.status)))
    if (!processing.length) return
    const t = setInterval(async () => {
      for (const item of processing) {
        if (!item.id) continue
        try {
          const r = await getDocStatus(item.id)
          const d = r.data
          const status = norm(d.statut)
          const zone = norm(d.zone)
          const stageIdx = STAGES.indexOf(status)
          const progress = ZONE_PCT[zone] || (stageIdx >= 0 ? Math.round((stageIdx + 1) / STAGES.length * 100) : 10)
          setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status, zone, progress, pipeline: d.pipeline_steps } : q))
          // Refresh docs quand un traitement termine
          if (['valide','anomalie'].includes(status)) { loadDocs(); loadStats() }
        } catch {}
      }
    }, 2000)
    return () => clearInterval(t)
  }, [queue])

  const filtered = docs.filter(d => {
    if (filter.status && !d.statut?.toLowerCase().includes(filter.status)) return false
    if (filter.type && !d.type_document?.toLowerCase().includes(filter.type)) return false
    if (filter.q) {
      const q = filter.q.toLowerCase()
      return [d.nom_fichier, d.nom_fournisseur, d.numero_siren].some(v => v?.toLowerCase().includes(q))
    }
    return true
  })

  const byType = Object.entries(stats?.documents?.by_type || {}).map(([k,v]) => ({
    name: { facture:'Facture', devis:'Devis', kbis:'KBIS', rib:'RIB',
            attestation_urssaf:'URSSAF', attestation_fiscale:'Fiscal', autre:'Autre' }[k] || k,
    count: v
  }))
  const byZone = Object.entries(stats?.documents?.by_zone || {}).map(([k,v]) => ({ name: k.toUpperCase(), value: v }))

  if (loading) return <Spinner />

  return (
    <div>
      <div className="flex items-start justify-between pt-8 px-8 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold">Dashboard</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>Vue d'ensemble et traitement des documents</p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={() => { loadStats(); loadDocs() }}><RefreshCw size={14} className="inline mr-1" />Refresh</Btn>
          <Btn variant="primary" size="sm" onClick={() => document.getElementById('dropzone-trigger')?.click()}>
            <Upload size={14} className="inline mr-1" />Upload
          </Btn>
        </div>
      </div>

      <div className="px-8 space-y-5">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard label="Documents traités"  value={stats?.documents?.total}        delta="Total"         color="accent" />
          <KpiCard label="Montant facturé"    value={`${(stats?.financials?.total_invoiced||0).toLocaleString('fr-FR')} €`} delta="Factures" color="success" />
          <KpiCard label="Alertes fraude"     value={stats?.documents?.fraudulent}    delta="Suspects"      color="danger" />
          <KpiCard label="Fournisseurs"       value={stats?.suppliers?.total}         delta="En base"       color="accent" />
        </div>

        {/* Alerte fraude */}
        {(stats?.documents?.fraudulent || 0) > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl" style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid var(--danger)' }}>
            <AlertTriangle size={20} style={{ color: 'var(--danger)' }} />
            <span style={{ color: 'var(--danger)' }} className="font-medium">
              {stats.documents.fraudulent} document(s) suspect(s) — voir Conformité
            </span>
          </div>
        )}

        {/* Upload zone */}
        <div {...getRootProps()} id="dropzone-trigger" className="rounded-xl p-6 text-center cursor-pointer transition-all"
             style={{
               border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
               background: isDragActive ? 'rgba(108,99,255,0.06)' : 'var(--surface)',
             }}>
          <input {...getInputProps()} />
          <Upload size={32} className="mx-auto mb-2" style={{ color: isDragActive ? 'var(--accent)' : 'var(--text2)' }} />
          <div className="font-medium text-sm">
            {isDragActive ? 'Relâchez pour uploader' : 'Déposez vos documents ici ou cliquez'}
          </div>
          <p className="text-xs mt-1" style={{ color: 'var(--text2)' }}>PDF, JPEG, PNG, TIFF — max 20 fichiers</p>
          {uploading && <div className="mt-2 flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--accent)' }}>
            <Loader size={14} className="animate-spin" /> Upload en cours...
          </div>}
        </div>

        {/* Queue traitement */}
        {queue.length > 0 && (
          <Panel title={`Traitement en cours — ${queue.filter(q => !['valide','anomalie','error'].includes(norm(q.status))).length} restant(s)`}>
            <div className="divide-y" style={{ divideColor: 'var(--border)' }}>
              {queue.map(item => (
                <div key={item.id || item.filename} className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div className="text-lg">
                      {norm(item.status) === 'valide' ? '✅' : norm(item.status) === 'anomalie' ? '⚠️' : norm(item.status) === 'error' ? '❌' : '⚙️'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{item.filename}</div>
                    </div>
                    <StatusPill status={item.status} />
                  </div>
                  {!['valide','anomalie','rejete','error'].includes(norm(item.status)) && (
                    <div className="h-1.5 rounded-full mt-2 overflow-hidden" style={{ background: 'var(--border)' }}>
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{ width: `${item.progress || 10}%`, background: 'linear-gradient(90deg, var(--accent), var(--accent2))' }} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Panel>
        )}

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ background: 'var(--surface2)' }}>
          {[['overview','Vue d\'ensemble'],['documents','Documents']].map(([k,l]) => (
            <button key={k} onClick={() => setTab(k)}
              className="px-4 py-2 rounded-md text-sm font-medium transition-all"
              style={{ background: tab===k ? 'var(--accent)' : 'transparent', color: tab===k ? 'white' : 'var(--text2)' }}>
              {l}
            </button>
          ))}
        </div>

        {/* Overview */}
        {tab === 'overview' && (
          <div className="grid grid-cols-3 gap-5">
            <Panel title="Documents par type" className="col-span-2">
              <div className="p-4 h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={byType} barSize={28}>
                    <XAxis dataKey="name" tick={{ fill: 'var(--text2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: 'var(--text2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8 }} />
                    <Bar dataKey="count" fill="var(--accent)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>

            <Panel title="Data Lake">
              <div className="p-4 h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={byZone} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70}
                         label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                      {byZone.map((_, i) => <Cell key={i} fill={['#cd7f32','#c0c0c0','#ffd700'][i] || COLORS[i]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Panel>
          </div>
        )}

        {/* Documents list */}
        {tab === 'documents' && (
          <>
            <div className="flex gap-3 flex-wrap">
              <input className="rounded-lg px-3 py-2 text-sm flex-1 min-w-48"
                     style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                     placeholder="Rechercher..." value={filter.q} onChange={e => setFilter(p => ({ ...p, q: e.target.value }))} />
              <select className="rounded-lg px-3 py-2 text-sm"
                      style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                      value={filter.status} onChange={e => setFilter(p => ({ ...p, status: e.target.value }))}>
                {[['','Tous statuts'],['valide','Validé'],['anomalie','Anomalie'],['en_traitement','En cours']].map(([v,l]) =>
                  <option key={v} value={v}>{l}</option>)}
              </select>
            </div>

            <Panel>
              {docsLoading ? <Spinner /> : filtered.length === 0 ? <Empty title="Aucun document" sub="Uploadez des fichiers pour commencer" /> : (
                <Table headers={['Fichier','Type','Fournisseur','Montant TTC','Fraude','Statut']}>
                  {filtered.map(d => (
                    <Tr key={d.id} onClick={() => setSelected(d)}>
                      <Td><span className="font-medium text-xs max-w-48 truncate block">{d.nom_fichier}</span></Td>
                      <Td><TypeBadge type={d.type_document} /></Td>
                      <Td><span className="text-xs">{d.nom_fournisseur || '—'}</span></Td>
                      <Td><span className="font-mono text-xs">{d.montant_ttc ? `${d.montant_ttc.toFixed(2)} €` : '—'}</span></Td>
                      <Td><FraudScore score={d.score_fraude} /></Td>
                      <Td><StatusPill status={d.statut} /></Td>
                    </Tr>
                  ))}
                </Table>
              )}
            </Panel>
          </>
        )}
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="fixed inset-0 z-50 flex" onClick={() => setSelected(null)}>
          <div className="flex-1" />
          <div className="w-[480px] h-full overflow-y-auto shadow-2xl slide-in"
               style={{ background: 'var(--surface)', borderLeft: '1px solid var(--border)' }}
               onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 flex items-center justify-between p-5 border-b"
                 style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <div className="font-display font-bold text-lg">Détail document</div>
              <button onClick={() => setSelected(null)} style={{ color: 'var(--text2)' }}>✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex gap-2 flex-wrap">
                <StatusPill status={selected.statut} />
                <TypeBadge type={selected.type_document} />
                <ZoneBadge zone={selected.zone} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['Fournisseur', selected.nom_fournisseur],
                  ['SIREN', selected.numero_siren],
                  ['Montant TTC', selected.montant_ttc ? `${selected.montant_ttc} €` : null],
                  ['Date', selected.date_document],
                  ['Score Fraude', selected.score_fraude ? `${(selected.score_fraude*100).toFixed(0)}%` : '0%'],
                ].map(([l,v]) => v ? (
                  <div key={l}>
                    <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>{l}</div>
                    <div className="text-sm font-medium mt-0.5">{v}</div>
                  </div>
                ) : null)}
              </div>
              {(selected.anomalies_count > 0) && (
                <div className="rounded-lg p-3" style={{ background: 'rgba(255,107,53,0.1)', border: '1px solid var(--warn)' }}>
                  <div className="font-bold text-sm" style={{ color: 'var(--warn)' }}>{selected.anomalies_count} anomalie(s)</div>
                </div>
              )}
              <div className="flex gap-2">
                <Btn variant="success" size="sm" onClick={async () => { await validateDoc(selected.id); toast.success('Validé'); setSelected(null); loadDocs() }}>Valider</Btn>
                <Btn variant="danger"  size="sm" onClick={async () => { await rejectDoc(selected.id); toast.success('Rejeté'); setSelected(null); loadDocs() }}>Rejeter</Btn>
                <Btn variant="ghost"   size="sm" onClick={async () => { await reprocessDoc(selected.id); toast.success('Relancé') }}>Relancer</Btn>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
