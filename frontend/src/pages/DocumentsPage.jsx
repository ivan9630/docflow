import React, { useState, useEffect } from 'react'
import { listDocuments, validateDoc, rejectDoc, reprocessDoc } from '../api'
import { Panel, StatusPill, TypeBadge, ZoneBadge, FraudScore, Table, Tr, Td, Spinner, Empty, Btn } from '../components/UI'
import toast from 'react-hot-toast'

export default function DocumentsPage() {
  const [docs, setDocs]     = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]  = useState({ status:'', type:'', q:'' })
  const [selected, setSelected] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const r = await listDocuments({ limit: 200 })
      setDocs(r.data.documents || [])
    } catch { toast.error('Erreur chargement') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const filtered = docs.filter(d => {
    if (filter.status && d.statut !== filter.status) return false
    if (filter.type   && d.type_document !== filter.type) return false
    if (filter.q) {
      const q = filter.q.toLowerCase()
      return [d.nom_fichier, d.nom_fournisseur, d.numero_siren, d.numero_document]
        .some(v => v?.toLowerCase().includes(q))
    }
    return true
  })

  const sel = (f) => (e) => setFilter(p => ({ ...p, [f]: e.target.value }))

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Documents</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>{docs.length} document(s) au total</p>
        </div>
        <Btn variant="ghost" size="sm" onClick={load}>↻ Actualiser</Btn>
      </div>

      <div className="px-8 space-y-4">
        {/* Filtres */}
        <div className="flex gap-3 flex-wrap">
          <input className="rounded-lg px-3 py-2 text-sm flex-1 min-w-48"
                 style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                 placeholder="🔍  Rechercher…" value={filter.q} onChange={sel('q')} />
          {[
            { key:'status', opts:[['','Tous statuts'],['valide','Validé'],['anomalie','Anomalie'],['en_traitement','En cours'],['rejete','Rejeté']] },
            { key:'type',   opts:[['','Tous types'],['facture','Facture'],['devis','Devis'],['attestation_urssaf','URSSAF'],['kbis','KBIS'],['rib','RIB']] },
          ].map(({ key, opts }) => (
            <select key={key} className="rounded-lg px-3 py-2 text-sm"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                    value={filter[key]} onChange={sel(key)}>
              {opts.map(([v,l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          ))}
        </div>

        {/* Table */}
        <Panel>
          {loading ? <Spinner /> : filtered.length === 0 ? <Empty title="Aucun document" sub="Uploadez des fichiers pour commencer" /> : (
            <Table headers={['Fichier','Type','Fournisseur','SIREN','Montant TTC','Zone','Fraude','Statut']}>
              {filtered.map(d => (
                <Tr key={d.id} onClick={() => setSelected(d)}>
                  <Td><span className="font-medium text-xs max-w-40 truncate block">{d.nom_fichier}</span></Td>
                  <Td><TypeBadge type={d.type_document} /></Td>
                  <Td><span className="text-xs">{d.nom_fournisseur || '—'}</span></Td>
                  <Td><span className="font-mono text-xs">{d.numero_siren || '—'}</span></Td>
                  <Td><span className="font-mono text-xs">{d.montant_ttc ? `${d.montant_ttc.toFixed(2)} €` : '—'}</span></Td>
                  <Td><ZoneBadge zone={d.zone} /></Td>
                  <Td><FraudScore score={d.score_fraude} /></Td>
                  <Td><StatusPill status={d.statut} /></Td>
                </Tr>
              ))}
            </Table>
          )}
        </Panel>
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
              <div>
                <div className="font-display font-bold text-lg">Détail document</div>
                <div className="font-mono text-xs mt-0.5" style={{ color: 'var(--text2)' }}>
                  {selected.id?.slice(0,8)}…
                </div>
              </div>
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
                  ['Montant HT', selected.montant_ht ? `${selected.montant_ht} €` : null],
                  ['Montant TTC', selected.montant_ttc ? `${selected.montant_ttc} €` : null],
                  ['TVA', selected.numero_tva],
                  ['IBAN', selected.iban],
                  ['Date', selected.date_document],
                  ['N° Document', selected.numero_document],
                  ['Score OCR', selected.score_ocr ? `${(selected.score_ocr*100).toFixed(0)}%` : null],
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
                  <div className="font-bold text-sm" style={{ color: 'var(--warn)' }}>⚠ {selected.anomalies_count} anomalie(s)</div>
                </div>
              )}
              <div className="flex gap-2">
                <Btn variant="success" size="sm" onClick={async () => { await validateDoc(selected.id); toast.success('Validé'); setSelected(null); load() }}>✓ Valider</Btn>
                <Btn variant="danger"  size="sm" onClick={async () => { await rejectDoc(selected.id); toast.success('Rejeté'); setSelected(null); load() }}>✗ Rejeter</Btn>
                <Btn variant="ghost"   size="sm" onClick={async () => { await reprocessDoc(selected.id); toast.success('Pipeline relancé') }}>↺ Relancer</Btn>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
