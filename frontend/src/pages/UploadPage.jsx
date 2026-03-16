import React, { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle, Clock, Loader } from 'lucide-react'
import { uploadDocuments, getDocStatus } from '../api'
import { Panel, ZoneBadge, StatusPill } from '../components/UI'
import toast from 'react-hot-toast'

const STAGES = ['uploade','en_traitement','ocr_ok','extrait','verifie','valide']
const STAGE_LABELS = { uploade:'Upload', en_traitement:'OCR', ocr_ok:'Extraction NER', extrait:'Zone Clean', verifie:'Vérification IA', valide:'Zone Curated' }
const ZONE_PCT = { raw:20, clean:60, curated:95, uploade:5 }

export default function UploadPage() {
  const [queue, setQueue]   = useState([])
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return
    setUploading(true)
    const form = new FormData()
    accepted.forEach(f => form.append('files', f))

    try {
      const r = await uploadDocuments(form)
      const results = r.data.results || []
      const newItems = results.map(res => ({
        id: res.doc_id, filename: res.filename,
        status: res.status === 'queued' ? 'en_traitement' : 'error',
        zone: 'raw', progress: 10, message: res.message,
        score_fraude: 0, anomalies: 0,
      }))
      setQueue(prev => [...newItems, ...prev])
      toast.success(`${r.data.uploaded} fichier(s) uploadé(s)`)
    } catch (e) {
      toast.error('Erreur upload: ' + (e.response?.data?.detail || e.message))
    } finally { setUploading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf':[], 'image/jpeg':[], 'image/png':[], 'image/tiff':[] },
    maxFiles: 20, maxSize: 50 * 1024 * 1024
  })

  // Polling des statuts
  useEffect(() => {
    const processing = queue.filter(q => !['valide','anomalie','rejete','error'].includes(q.status))
    if (!processing.length) return
    const t = setInterval(async () => {
      for (const item of processing) {
        if (!item.id) continue
        try {
          const r = await getDocStatus(item.id)
          const d = r.data
          setQueue(prev => prev.map(q => q.id === item.id ? {
            ...q, status: d.statut, zone: d.zone,
            score_fraude: d.score_fraude, anomalies: d.anomalies,
            progress: ZONE_PCT[d.zone] || STAGE_LABELS[d.statut] ? STAGES.indexOf(d.statut)/STAGES.length*100 : q.progress,
            pipeline: d.pipeline_steps,
          } : q))
        } catch {}
      }
    }, 3000)
    return () => clearInterval(t)
  }, [queue])

  return (
    <div>
      <div className="pt-8 px-8 mb-6">
        <h1 className="font-display text-2xl font-bold">Upload Multi-Documents</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
          PDF, JPEG, PNG, TIFF — max 20 fichiers × 50 MB
        </p>
      </div>
      <div className="px-8 space-y-6">

        {/* Drop Zone */}
        <div {...getRootProps()} className="rounded-2xl p-12 text-center cursor-pointer transition-all"
             style={{
               border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
               background: isDragActive ? 'rgba(108,99,255,0.06)' : 'var(--surface)',
             }}>
          <input {...getInputProps()} />
          <Upload size={48} className="mx-auto mb-4" style={{ color: isDragActive ? 'var(--accent)' : 'var(--text2)' }} />
          <div className="font-display text-lg font-bold mb-2">
            {isDragActive ? 'Relâchez pour uploader' : 'Déposez vos documents ici'}
          </div>
          <p className="text-sm" style={{ color: 'var(--text2)' }}>ou cliquez pour sélectionner — jusqu'à 20 fichiers simultanément</p>
          <div className="flex gap-2 justify-center mt-4 flex-wrap">
            {['PDF','JPEG','PNG','TIFF','50 MB max'].map(t => (
              <span key={t} className="px-3 py-1 rounded-full font-mono text-xs"
                    style={{ background: 'var(--surface2)', color: 'var(--text2)', border: '1px solid var(--border)' }}>{t}</span>
            ))}
          </div>
          {uploading && <div className="mt-4 flex items-center justify-center gap-2" style={{ color: 'var(--accent)' }}>
            <Loader size={16} className="animate-spin" /> Upload en cours…
          </div>}
        </div>

        {/* Queue */}
        {queue.length > 0 && (
          <Panel title={`File de traitement — ${queue.length} fichier(s)`}>
            <div className="divide-y" style={{ divideColor: 'var(--border)' }}>
              {queue.map(item => (
                <div key={item.id || item.filename} className="px-5 py-4">
                  <div className="flex items-center gap-4 mb-2">
                    <div className="text-2xl">
                      {item.status === 'valide'  ? '✅' :
                       item.status === 'anomalie'? '⚠️' :
                       item.status === 'error'   ? '❌' : '⚙️'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{item.filename}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <StatusPill status={item.status} />
                        {item.zone && <ZoneBadge zone={item.zone} />}
                        {item.score_fraude > 0 && (
                          <span className="font-mono text-xs"
                                style={{ color: item.score_fraude > 0.5 ? 'var(--danger)' : 'var(--warn)' }}>
                            Fraude: {Math.round(item.score_fraude*100)}%
                          </span>
                        )}
                        {item.anomalies > 0 && (
                          <span className="font-mono text-xs" style={{ color: 'var(--warn)' }}>
                            {item.anomalies} anomalie(s)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  {/* Barre de progression */}
                  {!['valide','anomalie','rejete','error'].includes(item.status) && (
                    <div className="h-1.5 rounded-full mt-2 overflow-hidden" style={{ background: 'var(--border)' }}>
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{ width: `${item.progress || 10}%`, background: 'linear-gradient(90deg, var(--accent), var(--accent2))' }} />
                    </div>
                  )}
                  {/* Étapes pipeline */}
                  {item.pipeline && item.pipeline.length > 0 && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {item.pipeline.map((s, i) => (
                        <span key={i} className="font-mono text-xs px-2 py-0.5 rounded"
                              style={{ background: 'var(--surface2)', color: 'var(--accent2)' }}>
                          ✓ {s.etape} ({s.ms}ms)
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>
    </div>
  )
}
