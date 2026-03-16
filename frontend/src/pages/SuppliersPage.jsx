import React, { useState, useEffect } from 'react'
import { listSuppliers, getSupplier, createSupplier, updateSupplier, supplierDocs, autofillCRM } from '../api'
import { Panel, Table, Tr, Td, Spinner, Empty, Btn, StatusPill } from '../components/UI'
import toast from 'react-hot-toast'

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [docs, setDocs] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [q, setQ] = useState('')
  const [form, setForm] = useState({
    nom:'', siren:'', siret_siege:'', numero_tva:'', iban:'',
    adresse:'', code_postal:'', ville:'', email:'', telephone:''
  })

  const load = async () => {
    setLoading(true)
    try { const r = await listSuppliers(); setSuppliers(r.data) }
    catch { toast.error('Erreur chargement') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const openDetail = async (id) => {
    setSelected(id)
    const [r1, r2] = await Promise.all([getSupplier(id), supplierDocs(id)])
    setDetail(r1.data); setDocs(r2.data.documents || [])
  }

  const handleCreate = async () => {
    if (!form.nom) { toast.error('Raison sociale requise'); return }
    try {
      await createSupplier(form)
      toast.success('Fournisseur créé'); setShowForm(false); load()
    } catch { toast.error('Erreur création') }
  }

  const handleAutofill = async () => {
    try { const r = await autofillCRM(); toast.success(r.data.message) }
    catch { toast.error('Erreur auto-fill') }
  }

  const filtered = suppliers.filter(s =>
    !q || [s.nom, s.siren, s.ville].some(v => v?.toLowerCase().includes(q.toLowerCase()))
  )

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">CRM Fournisseurs</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>Base de données fournisseurs — auto-remplie par l'IA</p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={handleAutofill}>⚡ Auto-fill depuis Curated</Btn>
          <Btn variant="primary" size="sm" onClick={() => setShowForm(true)}>+ Fournisseur</Btn>
        </div>
      </div>

      <div className="px-8 space-y-4">
        <input className="rounded-lg px-3 py-2 text-sm w-full max-w-md"
               style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
               placeholder="🔍  Rechercher fournisseur, SIREN, ville…" value={q}
               onChange={e => setQ(e.target.value)} />

        <Panel>
          {loading ? <Spinner /> : filtered.length === 0 ? <Empty title="Aucun fournisseur" sub="Uploadez des documents pour alimenter la BDD" /> : (
            <Table headers={['Raison sociale','SIREN','Ville','URSSAF','Score conformité','Blacklist','']}>
              {filtered.map(s => (
                <Tr key={s.id} onClick={() => openDetail(s.id)}>
                  <Td><span className="font-medium">{s.nom}</span></Td>
                  <Td><span className="font-mono text-xs">{s.siren || '—'}</span></Td>
                  <Td>{s.ville || '—'}</Td>
                  <Td>{s.attestation_urssaf_valide
                    ? <span style={{ color: 'var(--accent2)' }}>✓ Valide</span>
                    : <span style={{ color: 'var(--danger)' }}>✗ Manquante</span>}
                  </Td>
                  <Td>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border)', minWidth: 60 }}>
                        <div className="h-full rounded-full" style={{
                          width: `${s.score_conformite}%`,
                          background: s.score_conformite > 80 ? 'var(--accent2)' : s.score_conformite > 50 ? 'var(--warn)' : 'var(--danger)'
                        }} />
                      </div>
                      <span className="font-mono text-xs">{s.score_conformite?.toFixed(0)}%</span>
                    </div>
                  </Td>
                  <Td>{s.est_blackliste
                    ? <span className="font-bold" style={{ color: 'var(--danger)' }}>⚠ Blacklisté</span>
                    : <span style={{ color: 'var(--text2)' }}>—</span>}
                  </Td>
                  <Td><Btn variant="ghost" size="sm" onClick={e => { e.stopPropagation(); openDetail(s.id) }}>Voir</Btn></Td>
                </Tr>
              ))}
            </Table>
          )}
        </Panel>
      </div>

      {/* Detail panel */}
      {detail && (
        <div className="fixed inset-0 z-50 flex" onClick={() => { setSelected(null); setDetail(null) }}>
          <div className="flex-1" />
          <div className="w-[520px] h-full overflow-y-auto shadow-2xl slide-in"
               style={{ background: 'var(--surface)', borderLeft: '1px solid var(--border)' }}
               onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 flex items-center justify-between p-5 border-b"
                 style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <div>
                <div className="font-display font-bold text-lg">{detail.nom}</div>
                <div className="font-mono text-xs mt-0.5" style={{ color: 'var(--text2)' }}>SIREN: {detail.siren}</div>
              </div>
              <button onClick={() => { setSelected(null); setDetail(null) }} style={{ color: 'var(--text2)' }}>✕</button>
            </div>
            <div className="p-5 space-y-5">
              {/* Score conformité */}
              <div className="rounded-xl p-4" style={{ background: 'var(--surface2)' }}>
                <div className="text-center mb-3">
                  <div className="font-display text-3xl font-bold" style={{
                    color: detail.score_conformite > 80 ? 'var(--accent2)' : detail.score_conformite > 50 ? 'var(--warn)' : 'var(--danger)'
                  }}>{detail.score_conformite?.toFixed(0)}%</div>
                  <div className="text-xs" style={{ color: 'var(--text2)' }}>Score de conformité</div>
                </div>
                <div className="space-y-2">
                  {[
                    ['Attestation URSSAF', detail.attestation_urssaf_valide],
                    ['Attestation fiscale', detail.attestation_fiscale_valide],
                    ['IBAN enregistré', !!detail.iban],
                    ['Non blacklisté', !detail.est_blackliste],
                  ].map(([label, ok]) => (
                    <div key={label} className="flex items-center gap-2 text-sm">
                      <span style={{ color: ok ? 'var(--accent2)' : 'var(--danger)' }}>{ok ? '✓' : '✗'}</span>
                      {label}
                    </div>
                  ))}
                </div>
              </div>
              {/* Infos */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['SIRET siège', detail.siret_siege], ['N° TVA', detail.numero_tva],
                  ['IBAN', detail.iban], ['BIC', detail.bic],
                  ['Email', detail.email], ['Téléphone', detail.telephone],
                  ['Forme juridique', detail.forme_juridique], ['Code NAF', detail.code_naf],
                ].map(([l, v]) => v ? (
                  <div key={l}>
                    <div className="font-mono text-xs uppercase tracking-wide" style={{ color: 'var(--text2)' }}>{l}</div>
                    <div className="text-xs font-medium mt-0.5 truncate">{v}</div>
                  </div>
                ) : null)}
              </div>
              {/* Docs récents */}
              {docs.length > 0 && (
                <div>
                  <div className="font-display font-bold text-sm mb-3">Documents récents</div>
                  <div className="space-y-2">
                    {docs.slice(0,5).map(d => (
                      <div key={d.id} className="flex items-center gap-3 rounded-lg p-3"
                           style={{ background: 'var(--surface2)' }}>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium truncate">{d.nom}</div>
                          <div className="font-mono text-xs mt-0.5" style={{ color: 'var(--text2)' }}>
                            {d.date || '—'} · {d.montant_ttc ? `${d.montant_ttc} €` : '—'}
                          </div>
                        </div>
                        <StatusPill status={d.statut} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {detail.est_blackliste && (
                <div className="rounded-lg p-3" style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid var(--danger)' }}>
                  <div className="font-bold text-sm" style={{ color: 'var(--danger)' }}>🚫 Fournisseur blacklisté</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>{detail.motif_blacklist}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modale création */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.7)' }}>
          <div className="rounded-2xl w-[540px] max-h-[85vh] overflow-y-auto"
               style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between p-5 border-b" style={{ borderColor: 'var(--border)' }}>
              <div className="font-display font-bold text-lg">Nouveau Fournisseur</div>
              <button onClick={() => setShowForm(false)} style={{ color: 'var(--text2)' }}>✕</button>
            </div>
            <div className="p-5 grid grid-cols-2 gap-4">
              {Object.keys(form).map(k => (
                <div key={k} className={k === 'nom' || k === 'adresse' ? 'col-span-2' : ''}>
                  <label className="font-mono text-xs uppercase tracking-wide block mb-1" style={{ color: 'var(--text2)' }}>
                    {k.replace(/_/g,' ')} {k==='nom'?'*':''}
                  </label>
                  <input className="w-full rounded-lg px-3 py-2 text-sm"
                         style={{ background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                         value={form[k]} onChange={e => setForm(p => ({ ...p, [k]: e.target.value }))} />
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 p-5 border-t" style={{ borderColor: 'var(--border)' }}>
              <Btn variant="ghost" onClick={() => setShowForm(false)}>Annuler</Btn>
              <Btn variant="primary" onClick={handleCreate}>Créer</Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
