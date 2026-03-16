import React, { useEffect, useState, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { RefreshCw, AlertTriangle, TrendingUp } from 'lucide-react'
import { dashboardStats, autofillCRM, triggerDAG } from '../api'
import { KpiCard, Panel, Btn, Spinner } from '../components/UI'
import toast from 'react-hot-toast'

const COLORS = ['#6c63ff','#00d4aa','#ff6b35','#ffd166','#ff3366','#8b85ff']

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const r = await dashboardStats()
      setStats(r.data)
    } catch { toast.error('Impossible de charger les stats') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load(); const i = setInterval(load, 20000); return () => clearInterval(i) }, [load])

  const handleAutofill = async () => {
    try { await autofillCRM(); toast.success('CRM mis à jour depuis la zone Curated') }
    catch { toast.error('Erreur auto-fill CRM') }
  }

  const handleTrigger = async () => {
    try { await triggerDAG('docuflow_pipeline'); toast.success('DAG Airflow déclenché') }
    catch { toast.error('Airflow non disponible') }
  }

  if (loading) return <Spinner />

  const byType = Object.entries(stats?.documents?.by_type || {}).map(([k,v]) => ({
    name: { facture:'Facture', devis:'Devis', kbis:'KBIS', rib:'RIB',
            attestation_urssaf:'URSSAF', attestation_fiscale:'Fiscal', autre:'Autre' }[k] || k,
    count: v
  }))

  const byStatus = Object.entries(stats?.documents?.by_status || {}).map(([k,v]) => ({
    name: { valide:'Validé', anomalie:'Anomalie', en_traitement:'En cours',
            traite:'Traité', uploade:'Uploadé', rejete:'Rejeté', verifie:'Vérifié' }[k] || k,
    value: v
  }))

  const byZone = Object.entries(stats?.documents?.by_zone || {}).map(([k,v]) => ({ name: k.toUpperCase(), value: v }))

  return (
    <div>
      <div className="flex items-start justify-between pt-8 px-8 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold">Dashboard</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
            Vue d'ensemble temps réel — DocuFlow v2
          </p>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" size="sm" onClick={load}><RefreshCw size={14} className="inline mr-1" />Refresh</Btn>
          <Btn variant="secondary" size="sm" onClick={handleAutofill}>⚡ Auto-fill CRM</Btn>
          <Btn variant="primary" size="sm" onClick={handleTrigger}>▶ Trigger Airflow</Btn>
        </div>
      </div>

      <div className="px-8 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard label="Documents traités"  value={stats?.documents?.total}     delta="Total pipeline"         color="accent" />
          <KpiCard label="Montant facturé"    value={`${(stats?.financials?.total_invoiced||0).toLocaleString('fr-FR')} €`} delta="Factures validées" color="success" />
          <KpiCard label="Alertes fraude"     value={stats?.documents?.fraudulent} delta="Documents suspects"      color="danger" />
          <KpiCard label="Anomalies ouvertes" value={stats?.anomalies?.open}       delta="À traiter"              color="warning" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <KpiCard label="Fournisseurs"   value={stats?.suppliers?.total}      delta="BDD fournisseurs"  color="accent" />
          <KpiCard label="Blacklistés"    value={stats?.suppliers?.blacklisted} delta="Fraudes avérées"  color="danger" />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-3 gap-6">
          <Panel title="Documents par type" className="col-span-2">
            <div className="p-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byType} barSize={28}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8 }}
                           labelStyle={{ color: 'var(--text)' }} itemStyle={{ color: 'var(--accent)' }} />
                  <Bar dataKey="count" fill="var(--accent)" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title="Data Lake zones">
            <div className="p-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={byZone} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                       label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                    {byZone.map((_, i) => <Cell key={i} fill={['#cd7f32','#c0c0c0','#ffd700'][i] || COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>

        {/* Alerte fraude */}
        {(stats?.documents?.fraudulent || 0) > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl" style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid var(--danger)' }}>
            <AlertTriangle size={20} style={{ color: 'var(--danger)' }} />
            <span style={{ color: 'var(--danger)' }} className="font-medium">
              {stats.documents.fraudulent} document(s) frauduleux détecté(s) — intervention requise
            </span>
            <Btn variant="danger" size="sm" className="ml-auto" onClick={() => window.location.href='/compliance'}>
              Voir les alertes
            </Btn>
          </div>
        )}

        {/* Architecture Médaillon */}
        <Panel title="Architecture Data Lake — Médaillon">
          <div className="p-6 flex items-center justify-center gap-4 flex-wrap">
            {[
              { zone:'RAW',     color:'#cd7f32', icon:'🟤', desc:'Fichiers bruts\nimmuables' },
              { zone:'CLEAN',   color:'#c0c0c0', icon:'⚪', desc:'Texte OCR\n+ entités JSON' },
              { zone:'CURATED', color:'#ffd700', icon:'🟡', desc:'Données enrichies\nIA, prêtes métier' },
            ].map(({ zone, color, icon, desc }, i) => (
              <React.Fragment key={zone}>
                <div className="text-center rounded-xl p-5 min-w-36"
                     style={{ border: `2px solid ${color}`, background: `${color}18` }}>
                  <div className="text-3xl mb-2">{icon}</div>
                  <div className="font-display font-bold text-sm" style={{ color }}>{zone}</div>
                  <div className="text-xs mt-1 whitespace-pre-line" style={{ color: 'var(--text2)' }}>{desc}</div>
                  <div className="font-mono text-xs mt-2 font-bold" style={{ color }}>
                    {stats?.documents?.by_zone?.[zone.toLowerCase()] || 0} fichiers
                  </div>
                </div>
                {i < 2 && <div className="text-2xl" style={{ color: 'var(--accent)' }}>→</div>}
              </React.Fragment>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}
