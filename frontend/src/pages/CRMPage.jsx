import React, { useState, useCallback, useEffect } from 'react'
import { Upload, Loader, RefreshCw } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { uploadDocuments, getDocStatus, getDocument, listDocuments, listSuppliers, autofillCRM } from '../api'
import { Panel, Btn, Spinner, StatusPill, TypeBadge, Empty } from '../components/UI'
import toast from 'react-hot-toast'

const STAGES = ['uploade','en_traitement','ocr_ok','extrait','verifie','valide']
const ZONE_PCT = { raw:15, clean:50, curated:90 }
const norm = (s) => s ? s.replace('DocumentStatus.','').replace('DataZone.','').toLowerCase() : ''

/* ── Champ auto-rempli ────────────────────────────────────────── */
function AutoField({ label, value, delay }) {
  const [visible, setVisible] = useState(false)
  const [typed, setTyped] = useState('')
  const display = value ?? ''

  useEffect(() => {
    setVisible(false); setTyped('')
    if (!display) return
    const show = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(show)
  }, [value, delay])

  useEffect(() => {
    if (!visible || !display) return
    let i = 0; setTyped('')
    const iv = setInterval(() => { i++; setTyped(display.slice(0, i)); if (i >= display.length) clearInterval(iv) }, 20)
    return () => clearInterval(iv)
  }, [visible, display])

  if (!display) return null

  return (
    <div>
      <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="rounded-lg px-3 py-2 text-sm mt-1 transition-all duration-300"
           style={{
             background: visible ? 'var(--surface2)' : 'var(--surface)',
             border: `1px solid ${visible ? 'var(--accent)66' : 'var(--border)'}`,
           }}>
        {visible ? (typed || '\u00A0') : <span style={{ color: 'var(--text2)' }}>...</span>}
      </div>
    </div>
  )
}

export default function CRMPage() {
  // Upload
  const [queue, setQueue] = useState([])
  const [uploading, setUploading] = useState(false)

  // CRM auto-fill
  const [lastDoc, setLastDoc] = useState(null)
  const [filling, setFilling] = useState(false)

  // Fournisseurs
  const [suppliers, setSuppliers] = useState([])
  const [recentDocs, setRecentDocs] = useState([])

  const loadData = async () => {
    try {
      const [r1, r2] = await Promise.all([listSuppliers(), listDocuments({ limit: 20 })])
      setSuppliers(r1.data || [])
      setRecentDocs(r2.data.documents || [])
    } catch {}
  }

  useEffect(() => { loadData() }, [])

  // Upload
  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return
    setUploading(true)
    setLastDoc(null); setFilling(false)
    const form = new FormData()
    accepted.forEach(f => form.append('files', f))
    try {
      const r = await uploadDocuments(form)
      const results = r.data.results || []
      const newItems = results.map(res => ({
        id: res.doc_id, filename: res.filename,
        status: res.status === 'queued' ? 'en_traitement' : 'error',
        progress: 10,
      }))
      setQueue(prev => [...newItems, ...prev])
      toast.success(`${r.data.uploaded} fichier(s) en cours de traitement`)
    } catch { toast.error('Erreur upload') }
    finally { setUploading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf':[], 'image/jpeg':[], 'image/png':[], 'image/tiff':[] },
    maxFiles: 20, maxSize: 50 * 1024 * 1024
  })

  // Polling
  useEffect(() => {
    const processing = queue.filter(q => !['valide','anomalie','rejete','error'].includes(norm(q.status)))
    if (!processing.length) return
    const t = setInterval(async () => {
      for (const item of processing) {
        if (!item.id) continue
        try {
          const r = await getDocStatus(item.id)
          const status = norm(r.data.statut)
          const zone = norm(r.data.zone)
          const stageIdx = STAGES.indexOf(status)
          const progress = ZONE_PCT[zone] || (stageIdx >= 0 ? Math.round((stageIdx + 1) / STAGES.length * 100) : 10)
          setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status, progress } : q))

          // Quand terminé → charger le doc complet pour auto-remplissage
          if (['valide','anomalie'].includes(status)) {
            const full = await getDocument(item.id)
            setLastDoc(full.data)
            setFilling(false)
            setTimeout(() => setFilling(true), 300)
            loadData() // refresh fournisseurs
          }
        } catch {}
      }
    }, 2000)
    return () => clearInterval(t)
  }, [queue])

  const handleAutofill = async () => {
    try { await autofillCRM(); toast.success('CRM mis à jour depuis la zone Curated'); loadData() }
    catch { toast.error('Erreur auto-fill') }
  }

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">CRM Fournisseurs</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
            Upload de documents — Auto-remplissage de la base fournisseurs par l'IA
          </p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={loadData}><RefreshCw size={14} className="inline mr-1" />Refresh</Btn>
          <Btn variant="ghost" size="sm" onClick={handleAutofill}>Auto-fill depuis Curated</Btn>
        </div>
      </div>

      <div className="px-8 space-y-5">
        {/* Upload */}
        <div {...getRootProps()} className="rounded-xl p-6 text-center cursor-pointer transition-all"
             style={{
               border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
               background: isDragActive ? 'rgba(108,99,255,0.06)' : 'var(--surface)',
             }}>
          <input {...getInputProps()} />
          <Upload size={32} className="mx-auto mb-2" style={{ color: isDragActive ? 'var(--accent)' : 'var(--text2)' }} />
          <div className="font-medium text-sm">{isDragActive ? 'Relâchez pour uploader' : 'Déposez vos documents ici'}</div>
          <p className="text-xs mt-1" style={{ color: 'var(--text2)' }}>PDF, JPEG, PNG — Les données fournisseur seront extraites automatiquement</p>
          {uploading && <div className="mt-2 flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--accent)' }}>
            <Loader size={14} className="animate-spin" /> Upload en cours...
          </div>}
        </div>

        {/* Queue */}
        {queue.length > 0 && (
          <div className="space-y-2">
            {queue.map(item => (
              <div key={item.id} className="flex items-center gap-3 rounded-lg px-4 py-3" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                <div className="text-lg">
                  {norm(item.status) === 'valide' ? '✅' : norm(item.status) === 'anomalie' ? '⚠️' : norm(item.status) === 'error' ? '❌' : '⚙️'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{item.filename}</div>
                  {!['valide','anomalie','error'].includes(norm(item.status)) && (
                    <div className="h-1.5 rounded-full mt-1 overflow-hidden" style={{ background: 'var(--border)' }}>
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{ width: `${item.progress}%`, background: 'linear-gradient(90deg, var(--accent), var(--accent2))' }} />
                    </div>
                  )}
                </div>
                <StatusPill status={item.status} />
              </div>
            ))}
          </div>
        )}

        {/* Auto-remplissage CRM */}
        {lastDoc && filling && (
          <Panel title="Fournisseur détecté — Auto-rempli par l'IA">
            <div className="p-5 space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                     style={{ background: 'var(--accent)22', border: '1px solid var(--accent)44' }}>
                  <span style={{ color: 'var(--accent)' }} className="font-bold">
                    {(lastDoc.nom_fournisseur || '?')[0]?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <div className="font-display font-bold">{lastDoc.nom_fournisseur || 'Fournisseur inconnu'}</div>
                  <div className="text-xs" style={{ color: 'var(--text2)' }}>
                    Extrait de : {lastDoc.nom_fichier} · <TypeBadge type={lastDoc.type_document} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <AutoField label="Raison sociale" value={lastDoc.nom_fournisseur} delay={200} />
                <AutoField label="SIREN" value={lastDoc.numero_siren} delay={400} />
                <AutoField label="SIRET" value={lastDoc.numero_siret} delay={600} />
                <AutoField label="N° TVA" value={lastDoc.numero_tva} delay={800} />
                <AutoField label="IBAN" value={lastDoc.iban} delay={1000} />
                <AutoField label="Numéro document" value={lastDoc.numero_document} delay={1200} />
                <AutoField label="Date document" value={lastDoc.date_document} delay={1400} />
                <AutoField label="Montant TTC" value={lastDoc.montant_ttc != null ? `${lastDoc.montant_ttc} €` : null} delay={1600} />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <StatusPill status={lastDoc.statut} />
                {lastDoc.score_fraude > 0 && (
                  <span className="font-mono text-xs" style={{ color: lastDoc.score_fraude > 0.5 ? 'var(--danger)' : 'var(--warn)' }}>
                    Fraude: {Math.round(lastDoc.score_fraude * 100)}%
                  </span>
                )}
                {lastDoc.anomalies_count > 0 && (
                  <span className="text-xs" style={{ color: 'var(--warn)' }}>{lastDoc.anomalies_count} anomalie(s)</span>
                )}
              </div>
            </div>
          </Panel>
        )}

        {/* Base fournisseurs */}
        <Panel title={`Base fournisseurs — ${suppliers.length} enregistré(s)`}>
          {suppliers.length === 0 ? <Empty title="Aucun fournisseur" sub="Uploadez des documents pour alimenter la base" /> : (
            <div className="divide-y" style={{ divideColor: 'var(--border)' }}>
              {suppliers.map(s => (
                <div key={s.id} className="flex items-center gap-4 px-5 py-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                       style={{ background: s.est_blackliste ? 'rgba(255,51,102,0.1)' : 'var(--surface2)' }}>
                    <span className="font-bold text-xs" style={{ color: s.est_blackliste ? 'var(--danger)' : 'var(--accent)' }}>
                      {(s.nom || '?')[0]?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{s.nom}</div>
                    <div className="text-xs" style={{ color: 'var(--text2)' }}>
                      SIREN: {s.siren || '—'} · {s.ville || '—'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.attestation_urssaf_valide
                      ? <span className="text-xs" style={{ color: 'var(--accent2)' }}>URSSAF ✓</span>
                      : <span className="text-xs" style={{ color: 'var(--danger)' }}>URSSAF ✗</span>
                    }
                    <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
                      <div className="h-full rounded-full" style={{
                        width: `${s.score_conformite || 0}%`,
                        background: (s.score_conformite || 0) > 80 ? 'var(--accent2)' : (s.score_conformite || 0) > 50 ? 'var(--warn)' : 'var(--danger)'
                      }} />
                    </div>
                    <span className="font-mono text-xs">{s.score_conformite?.toFixed(0)}%</span>
                  </div>
                  {s.est_blackliste && <span className="text-xs font-bold" style={{ color: 'var(--danger)' }}>BLACKLISTÉ</span>}
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  )
}
