import React, { useState, useCallback, useEffect } from 'react'
import { Upload, Loader, RefreshCw, CheckCircle2, AlertTriangle, XCircle, Search, X, FileText, ChevronRight } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { uploadDocuments, getDocStatus, getDocument, listDocuments, listSuppliers, getSupplier, supplierDocs, autofillCRM, dashboardStats } from '../api'
import { Panel, Btn, Spinner, StatusPill, TypeBadge, Empty, KpiCard } from '../components/UI'
import toast from 'react-hot-toast'

const STAGES = ['uploade','en_traitement','ocr_ok','extrait','verifie','valide']
const ZONE_PCT = { raw:15, clean:50, curated:90 }
const norm = (s) => s ? s.replace('DocumentStatus.','').replace('DataZone.','').toLowerCase() : ''

function AutoField({ label, value, delay }) {
  const [visible, setVisible] = useState(false)
  const [typed, setTyped] = useState('')
  const display = value ?? ''
  useEffect(() => { setVisible(false); setTyped(''); if (!display) return; const t = setTimeout(() => setVisible(true), delay); return () => clearTimeout(t) }, [value, delay])
  useEffect(() => { if (!visible || !display) return; let i = 0; setTyped(''); const iv = setInterval(() => { i++; setTyped(display.slice(0, i)); if (i >= display.length) clearInterval(iv) }, 20); return () => clearInterval(iv) }, [visible, display])
  if (!display) return null
  return (
    <div>
      <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="rounded-lg px-3 py-2 text-sm transition-all duration-300"
           style={{ background: visible ? 'var(--surface2)' : 'var(--surface)', border: `1px solid ${visible ? 'var(--accent)' : 'var(--border)'}` }}>
        {visible ? (typed || '\u00A0') : <span style={{ color: 'var(--text2)' }}>...</span>}
      </div>
    </div>
  )
}

export default function CRMPage() {
  const [queue, setQueue] = useState([])
  const [uploading, setUploading] = useState(false)
  const [lastDoc, setLastDoc] = useState(null)
  const [filling, setFilling] = useState(false)
  const [suppliers, setSuppliers] = useState([])
  const [recentDocs, setRecentDocs] = useState([])
  const [kpis, setKpis] = useState(null)
  const [search, setSearch] = useState('')

  // Fiche fournisseur
  const [selectedSup, setSelectedSup] = useState(null)
  const [supDetail, setSupDetail] = useState(null)
  const [supDocs, setSupDocs] = useState([])
  const [supLoading, setSupLoading] = useState(false)

  const loadData = async () => {
    try {
      const [r1, r2, r3] = await Promise.all([listSuppliers(), listDocuments({ limit: 10 }), dashboardStats()])
      setSuppliers(r1.data || [])
      setRecentDocs(r2.data.documents || [])
      setKpis(r3.data)
    } catch {}
  }

  useEffect(() => { loadData() }, [])

  const loadSupplier = async (id) => {
    setSelectedSup(id); setSupLoading(true)
    try {
      const [r1, r2] = await Promise.all([getSupplier(id), supplierDocs(id)])
      setSupDetail(r1.data); setSupDocs(r2.data.documents || [])
    } catch { toast.error('Erreur chargement fournisseur') }
    finally { setSupLoading(false) }
  }

  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return
    setUploading(true); setLastDoc(null); setFilling(false)
    const form = new FormData()
    accepted.forEach(f => form.append('files', f))
    try {
      const r = await uploadDocuments(form)
      const newItems = (r.data.results || []).map(res => ({ id: res.doc_id, filename: res.filename, status: res.status === 'queued' ? 'en_traitement' : 'error', progress: 10 }))
      setQueue(prev => [...newItems, ...prev])
      toast.success(`${r.data.uploaded} fichier(s) en traitement`)
    } catch { toast.error('Erreur upload') }
    finally { setUploading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf':[], 'image/jpeg':[], 'image/png':[], 'image/tiff':[] }, maxFiles: 20, maxSize: 50 * 1024 * 1024
  })

  useEffect(() => {
    const processing = queue.filter(q => !['valide','anomalie','rejete','error'].includes(norm(q.status)))
    if (!processing.length) return
    const t = setInterval(async () => {
      for (const item of processing) {
        if (!item.id) continue
        try {
          const r = await getDocStatus(item.id)
          const status = norm(r.data.statut), zone = norm(r.data.zone)
          const stageIdx = STAGES.indexOf(status)
          const progress = ZONE_PCT[zone] || (stageIdx >= 0 ? Math.round((stageIdx + 1) / STAGES.length * 100) : 10)
          setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status, progress } : q))
          if (['valide','anomalie'].includes(status)) {
            const full = await getDocument(item.id)
            setLastDoc(full.data); setFilling(false)
            setTimeout(() => setFilling(true), 300); loadData()
          }
        } catch {}
      }
    }, 2000)
    return () => clearInterval(t)
  }, [queue])

  const handleAutofill = async () => {
    try { await autofillCRM(); toast.success('CRM mis a jour'); loadData() }
    catch { toast.error('Erreur auto-fill') }
  }

  const statusIcon = (s) => {
    if (norm(s) === 'valide') return <CheckCircle2 size={18} style={{ color: 'var(--accent2)' }} />
    if (norm(s) === 'anomalie') return <AlertTriangle size={18} style={{ color: 'var(--warn)' }} />
    if (norm(s) === 'error') return <XCircle size={18} style={{ color: 'var(--danger)' }} />
    return <Loader size={18} className="animate-spin" style={{ color: 'var(--accent)' }} />
  }

  const filtered = suppliers.filter(s => {
    if (!search) return true
    const q = search.toLowerCase()
    return s.nom?.toLowerCase().includes(q) || s.siren?.includes(q) || s.ville?.toLowerCase().includes(q)
  })

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-lg font-bold">CRM Fournisseurs</h1>
          <p className="text-[13px] mt-0.5" style={{ color: 'var(--text2)' }}>Upload de documents et auto-remplissage par l'IA</p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={loadData}><RefreshCw size={13} className="inline mr-1" />Refresh</Btn>
          <Btn variant="secondary" size="sm" onClick={handleAutofill}>Auto-fill Curated</Btn>
        </div>
      </div>

      <div className="px-8 pb-8 space-y-5">
        {/* KPIs */}
        {kpis && (
          <div className="grid grid-cols-4 gap-3">
            <KpiCard label="Fournisseurs" value={kpis.suppliers?.total || 0} color="accent" />
            <KpiCard label="Documents traites" value={kpis.documents?.total || 0} color="success" />
            <KpiCard label="Anomalies ouvertes" value={kpis.anomalies?.open || 0} color="warning" />
            <KpiCard label="Total facture" value={`${(kpis.financials?.total_invoiced || 0).toLocaleString()} EUR`} color="gold" />
          </div>
        )}

        {/* Upload */}
        <div {...getRootProps()} className="rounded-xl p-8 text-center cursor-pointer transition-all"
             style={{ border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`, background: isDragActive ? 'rgba(59,91,219,0.04)' : 'var(--surface)' }}>
          <input {...getInputProps()} />
          <Upload size={28} className="mx-auto mb-2" style={{ color: isDragActive ? 'var(--accent)' : 'var(--text2)' }} />
          <div className="font-medium text-sm">{isDragActive ? 'Relachez pour uploader' : 'Deposez vos documents ici'}</div>
          <p className="text-xs mt-1" style={{ color: 'var(--text2)' }}>PDF, JPEG, PNG — max 20 fichiers, 50 MB chacun</p>
          {uploading && <div className="mt-3 flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--accent)' }}><Loader size={14} className="animate-spin" /> Upload en cours...</div>}
        </div>

        {/* Queue */}
        {queue.length > 0 && (
          <div className="space-y-2">
            {queue.map(item => (
              <div key={item.id} className="flex items-center gap-3 rounded-lg px-4 py-3 shadow-sm" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                {statusIcon(item.status)}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{item.filename}</div>
                  {!['valide','anomalie','error'].includes(norm(item.status)) && (
                    <div className="h-1 rounded-full mt-1.5 overflow-hidden" style={{ background: 'var(--surface2)' }}>
                      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${item.progress}%`, background: 'var(--accent)' }} />
                    </div>
                  )}
                </div>
                <StatusPill status={item.status} />
              </div>
            ))}
          </div>
        )}

        {/* Auto-fill */}
        {lastDoc && filling && (
          <Panel title="Fournisseur detecte — Auto-rempli par l'IA">
            <div className="p-5 space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold text-white" style={{ background: 'var(--accent)' }}>
                  {(lastDoc.nom_fournisseur || '?')[0]?.toUpperCase()}
                </div>
                <div>
                  <div className="font-semibold">{lastDoc.nom_fournisseur || 'Fournisseur inconnu'}</div>
                  <div className="text-xs" style={{ color: 'var(--text2)' }}>{lastDoc.nom_fichier} &middot; <TypeBadge type={lastDoc.type_document} /></div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <AutoField label="Raison sociale" value={lastDoc.nom_fournisseur} delay={200} />
                <AutoField label="SIREN" value={lastDoc.numero_siren} delay={400} />
                <AutoField label="SIRET" value={lastDoc.numero_siret} delay={600} />
                <AutoField label="N TVA" value={lastDoc.numero_tva} delay={800} />
                <AutoField label="IBAN" value={lastDoc.iban} delay={1000} />
                <AutoField label="Montant TTC" value={lastDoc.montant_ttc != null ? `${lastDoc.montant_ttc} EUR` : null} delay={1200} />
              </div>
            </div>
          </Panel>
        )}

        {/* Documents recents */}
        {recentDocs.length > 0 && (
          <Panel title={`Documents recents (${recentDocs.length})`}>
            <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
              {recentDocs.map(d => (
                <div key={d.id} className="flex items-center gap-3 px-5 py-2.5 hover:bg-gray-50 transition-colors">
                  <FileText size={16} style={{ color: 'var(--text2)' }} />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm truncate">{d.nom_fichier}</span>
                  </div>
                  <TypeBadge type={d.type_document?.replace('DocumentType.', '')} />
                  <StatusPill status={norm(d.statut)} />
                  <span className="text-xs" style={{ color: 'var(--text2)' }}>{d.nom_fournisseur || '—'}</span>
                  {d.montant_ttc != null && <span className="text-xs font-semibold">{d.montant_ttc} EUR</span>}
                </div>
              ))}
            </div>
          </Panel>
        )}

        {/* Fournisseurs */}
        <div className={selectedSup ? 'grid grid-cols-5 gap-4' : ''}>
          <div className={selectedSup ? 'col-span-3' : ''}>
            <Panel title={`Base fournisseurs (${suppliers.length})`} action={
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--text2)' }} />
                <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                  placeholder="Rechercher nom, SIREN, ville..."
                  className="pl-8 pr-3 py-1.5 rounded-lg text-xs outline-none w-56"
                  style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }} />
                {search && <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2"><X size={12} style={{ color: 'var(--text2)' }} /></button>}
              </div>
            }>
              {filtered.length === 0 ? <Empty title="Aucun fournisseur" sub={search ? 'Aucun resultat pour cette recherche' : 'Uploadez des documents pour alimenter la base'} /> : (
                <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                  {filtered.map(s => (
                    <div key={s.id} onClick={() => loadSupplier(s.id)}
                         className="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 transition-colors cursor-pointer"
                         style={{ background: selectedSup === s.id ? 'rgba(59,91,219,0.04)' : 'transparent', borderLeft: selectedSup === s.id ? '3px solid var(--accent)' : '3px solid transparent' }}>
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold text-white"
                           style={{ background: s.est_blackliste ? 'var(--danger)' : 'var(--accent)' }}>
                        {(s.nom || '?')[0]?.toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{s.nom}</div>
                        <div className="text-xs" style={{ color: 'var(--text2)' }}>{s.siren || '—'} &middot; {s.ville || '—'}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-medium" style={{ color: s.attestation_urssaf_valide ? 'var(--accent2)' : 'var(--danger)' }}>
                          URSSAF {s.attestation_urssaf_valide ? 'OK' : 'KO'}
                        </span>
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
                          <div className="h-full rounded-full" style={{ width: `${s.score_conformite || 0}%`, background: (s.score_conformite || 0) > 80 ? 'var(--accent2)' : (s.score_conformite || 0) > 50 ? 'var(--warn)' : 'var(--danger)' }} />
                        </div>
                        <span className="text-xs font-semibold w-8 text-right">{s.score_conformite?.toFixed(0)}%</span>
                        <ChevronRight size={14} style={{ color: 'var(--text2)' }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>

          {/* Fiche fournisseur */}
          {selectedSup && (
            <div className="col-span-2 space-y-4">
              {supLoading ? <Spinner /> : supDetail && (
                <>
                  <Panel title="Fiche fournisseur">
                    <div className="p-5 space-y-3">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center text-base font-bold text-white"
                             style={{ background: supDetail.est_blackliste ? 'var(--danger)' : 'var(--accent)' }}>
                          {(supDetail.nom || '?')[0]?.toUpperCase()}
                        </div>
                        <div>
                          <div className="font-bold text-base">{supDetail.nom}</div>
                          <div className="text-xs" style={{ color: 'var(--text2)' }}>{supDetail.forme_juridique || ''} &middot; NAF {supDetail.code_naf || '—'}</div>
                        </div>
                        <button onClick={() => { setSelectedSup(null); setSupDetail(null) }} className="ml-auto p-1 rounded hover:bg-gray-100"><X size={16} style={{ color: 'var(--text2)' }} /></button>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {[
                          ['SIREN', supDetail.siren],
                          ['SIRET', supDetail.siret_siege],
                          ['N TVA', supDetail.numero_tva],
                          ['IBAN', supDetail.iban],
                          ['Adresse', supDetail.adresse],
                          ['Ville', [supDetail.code_postal, supDetail.ville].filter(Boolean).join(' ')],
                          ['Email', supDetail.email],
                          ['Telephone', supDetail.telephone],
                          ['Creation', supDetail.date_creation_entreprise],
                          ['KBIS', supDetail.kbis_date],
                        ].map(([label, val]) => (
                          <div key={label}>
                            <div className="text-xs" style={{ color: 'var(--text2)' }}>{label}</div>
                            <div className="font-medium truncate">{val || '—'}</div>
                          </div>
                        ))}
                      </div>

                      {/* Conformite */}
                      <div className="rounded-lg p-3 mt-2" style={{ background: 'var(--bg)' }}>
                        <div className="text-xs font-semibold mb-2">Conformite</div>
                        <div className="flex items-center gap-3 mb-2">
                          <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
                            <div className="h-full rounded-full" style={{
                              width: `${supDetail.score_conformite || 0}%`,
                              background: (supDetail.score_conformite || 0) > 80 ? 'var(--accent2)' : (supDetail.score_conformite || 0) > 50 ? 'var(--warn)' : 'var(--danger)'
                            }} />
                          </div>
                          <span className="text-sm font-bold">{supDetail.score_conformite?.toFixed(0)}%</span>
                        </div>
                        <div className="flex gap-4 text-xs">
                          <span style={{ color: supDetail.attestation_urssaf_valide ? 'var(--accent2)' : 'var(--danger)' }}>
                            URSSAF {supDetail.attestation_urssaf_valide ? 'OK' : 'KO'}
                            {supDetail.attestation_urssaf_date_exp && <span style={{ color: 'var(--text2)' }}> (exp. {supDetail.attestation_urssaf_date_exp})</span>}
                          </span>
                          <span style={{ color: supDetail.attestation_fiscale_valide ? 'var(--accent2)' : 'var(--danger)' }}>
                            Fiscal {supDetail.attestation_fiscale_valide ? 'OK' : 'KO'}
                          </span>
                        </div>
                        {supDetail.est_blackliste && (
                          <div className="mt-2 text-xs font-semibold" style={{ color: 'var(--danger)' }}>BLACKLISTE : {supDetail.motif_blacklist || 'Raison non specifiee'}</div>
                        )}
                      </div>
                    </div>
                  </Panel>

                  {/* Documents lies */}
                  <Panel title={`Documents lies (${supDocs.length})`}>
                    {supDocs.length === 0 ? <Empty title="Aucun document" sub="Pas de documents lies a ce fournisseur" /> : (
                      <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                        {supDocs.map(d => (
                          <div key={d.id} className="flex items-center gap-3 px-5 py-2.5">
                            <FileText size={14} style={{ color: 'var(--text2)' }} />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm truncate">{d.nom}</div>
                            </div>
                            <TypeBadge type={d.type?.replace('DocumentType.', '')} />
                            <StatusPill status={norm(d.statut)} />
                            {d.montant_ttc != null && <span className="text-xs font-semibold">{d.montant_ttc} EUR</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </Panel>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
