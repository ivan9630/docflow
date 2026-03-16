import React, { useState, useEffect } from 'react'
import { datalakeStats, datalakeZone } from '../api'
import { Panel, Spinner, Btn } from '../components/UI'
import toast from 'react-hot-toast'

export default function DataLakePage() {
  const [stats, setStats]   = useState(null)
  const [zone, setZone]     = useState('raw')
  const [objects, setObjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    datalakeStats().then(r => { setStats(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const loadZone = async (z) => {
    setZone(z)
    try {
      const r = await datalakeZone(z)
      setObjects(r.data.objects || [])
    } catch { toast.error('Erreur chargement zone') }
  }

  const ZONES = [
    { key:'raw',     label:'🟤 RAW',     color:'#cd7f32', desc:'Fichiers bruts immuables — ingestion directe' },
    { key:'clean',   label:'⚪ CLEAN',   color:'#c0c0c0', desc:'Texte OCR + entités JSON extraites' },
    { key:'curated', label:'🟡 CURATED', color:'#ffd700', desc:'Données enrichies IA, prêtes pour CRM & conformité' },
  ]

  return (
    <div>
      <div className="pt-8 px-8 mb-6">
        <h1 className="font-display text-2xl font-bold">Data Lake — Architecture Médaillon</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
          Stockage distribué MinIO compatible S3 — 3 zones structurées
        </p>
      </div>

      <div className="px-8 space-y-6">
        {/* Zone cards */}
        {loading ? <Spinner /> : (
          <div className="grid grid-cols-3 gap-5">
            {ZONES.map(({ key, label, color, desc }) => (
              <button key={key} onClick={() => loadZone(key)}
                className="rounded-xl p-5 text-left transition-all hover:scale-[1.02]"
                style={{
                  background: 'var(--surface)',
                  border: `2px solid ${zone === key ? color : 'var(--border)'}`,
                }}>
                <div className="font-display font-bold text-lg mb-1" style={{ color }}>{label}</div>
                <div className="text-xs mb-4" style={{ color: 'var(--text2)' }}>{desc}</div>
                <div className="font-display text-3xl font-bold" style={{ color }}>
                  {stats?.[key]?.count ?? 0}
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>fichiers</div>
                <div className="font-mono text-xs mt-1" style={{ color: 'var(--text2)' }}>
                  {stats?.[key]?.size_mb ?? 0} MB
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Architecture diagram */}
        <Panel title="Pipeline de transformation">
          <div className="p-6">
            <div className="flex items-center gap-3 flex-wrap justify-center">
              {[
                { label:'Upload',   icon:'📤', sub:'PDF / Images' },
                { label:'→', icon:'', sub:'' },
                { label:'OCR',      icon:'🔍', sub:'Tesseract + OpenCV' },
                { label:'→', icon:'', sub:'' },
                { label:'NER',      icon:'🧠', sub:'spaCy + Regex' },
                { label:'→', icon:'', sub:'' },
                { label:'RAW',      icon:'🟤', sub:'MinIO bucket', color:'#cd7f32' },
                { label:'→', icon:'', sub:'' },
                { label:'CLEAN',    icon:'⚪', sub:'MinIO bucket', color:'#c0c0c0' },
                { label:'→', icon:'', sub:'' },
                { label:'Claude IA',icon:'🤖', sub:'Enrichissement' },
                { label:'→', icon:'', sub:'' },
                { label:'CURATED',  icon:'🟡', sub:'MinIO bucket', color:'#ffd700' },
                { label:'→', icon:'', sub:'' },
                { label:'CRM / Conformité', icon:'🏢', sub:'Auto-fill', color:'var(--accent)' },
              ].map((s, i) => s.label === '→' ? (
                <span key={i} className="text-xl" style={{ color: 'var(--accent)' }}>→</span>
              ) : (
                <div key={i} className="text-center rounded-xl p-3 min-w-24"
                     style={{ border: `1px solid ${s.color || 'var(--border)'}`, background: s.color ? `${s.color}15` : 'var(--surface2)' }}>
                  <div className="text-2xl">{s.icon}</div>
                  <div className="font-display font-bold text-xs mt-1" style={{ color: s.color || 'var(--text)' }}>{s.label}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        {/* Zone explorer */}
        {objects.length > 0 && (
          <Panel title={`Objets — Zone ${zone.toUpperCase()}`}
                 action={<span className="font-mono text-xs" style={{ color: 'var(--text2)' }}>{objects.length} objet(s)</span>}>
            <div className="max-h-64 overflow-y-auto">
              {objects.map((o, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-b text-xs"
                     style={{ borderColor: 'var(--border)' }}>
                  <span className="font-mono flex-1 truncate" style={{ color: 'var(--text2)' }}>{o.name}</span>
                  <span className="font-mono" style={{ color: 'var(--text2)' }}>{(o.size/1024).toFixed(1)} KB</span>
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>
    </div>
  )
}
