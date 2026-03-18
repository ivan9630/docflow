import React, { useState, useEffect } from 'react'
import { adminStats } from '../api'
import { Panel, Spinner, KpiCard } from '../components/UI'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'

const COLORS = ['#3b5bdb', '#0ca678', '#e67700', '#e03131', '#e8a500', '#5c7cfa', '#845ef7', '#339af0', '#20c997', '#ff922b', '#f06595']
const clean = (s) => s?.replace('DocumentType.', '').replace('DataZone.', '').replace('DocumentStatus.', '') || s

export default function AdminPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminStats()
      .then(r => setData(r.data))
      .catch(() => toast.error('Erreur chargement stats'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (!data) return null

  const typeData = Object.entries(data.documents.by_type).map(([k, v]) => ({ name: clean(k), value: v }))
  const zoneData = Object.entries(data.documents.by_zone).map(([k, v]) => ({ name: clean(k), value: v }))
  const statusData = Object.entries(data.documents.by_status).map(([k, v]) => ({ name: clean(k), value: v }))
  const pipelineData = Object.entries(data.pipeline.avg_time_ms).map(([k, v]) => ({ name: k, ms: v }))
  const anomSevData = Object.entries(data.anomalies.by_severity || {}).map(([k, v]) => ({ name: k, value: v }))
  const anomTypeData = Object.entries(data.anomalies.by_type || {}).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))

  return (
    <div>
      <div className="pt-8 px-8 mb-6">
        <h1 className="text-xl font-bold">Administration & Monitoring</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>Vue d'ensemble du systeme DocuFlow</p>
      </div>

      <div className="px-8 space-y-5">
        {/* KPIs overview */}
        <div className="grid grid-cols-5 gap-3">
          <KpiCard label="Documents" value={data.overview.total_documents} color="accent" />
          <KpiCard label="Fournisseurs" value={data.overview.total_suppliers} color="success" />
          <KpiCard label="Utilisateurs" value={data.overview.total_users} color="accent" />
          <KpiCard label="Anomalies ouvertes" value={data.anomalies.open} color="warning" />
          <KpiCard label="Total facture" value={`${data.overview.total_invoiced.toLocaleString()} EUR`} color="gold" />
        </div>

        {/* AI Quality */}
        <Panel title="Qualite IA">
          <div className="p-5">
            <div className="grid grid-cols-4 gap-4">
              <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Modele classificateur</div>
                <div className="text-sm font-bold">{data.ai_quality.classifier_model}</div>
              </div>
              <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Accuracy</div>
                <div className="text-2xl font-bold" style={{ color: 'var(--accent2)' }}>{data.ai_quality.classifier_accuracy}%</div>
                <div className="text-xs" style={{ color: 'var(--text2)' }}>{data.ai_quality.training_samples} samples, {data.ai_quality.classes} classes</div>
              </div>
              <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Confiance OCR moyenne</div>
                <div className="text-2xl font-bold" style={{ color: data.ai_quality.avg_ocr_confidence > 80 ? 'var(--accent2)' : 'var(--warn)' }}>
                  {data.ai_quality.avg_ocr_confidence}%
                </div>
              </div>
              <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Confiance classification</div>
                <div className="text-2xl font-bold" style={{ color: data.ai_quality.avg_classification_confidence > 80 ? 'var(--accent2)' : 'var(--warn)' }}>
                  {data.ai_quality.avg_classification_confidence}%
                </div>
              </div>
            </div>

            {/* Fraude */}
            <div className="mt-4 flex items-center gap-4 rounded-lg p-4" style={{ background: 'var(--bg)' }}>
              <div>
                <div className="text-xs font-medium" style={{ color: 'var(--text2)' }}>Taux de fraude detecte</div>
                <div className="text-2xl font-bold" style={{ color: data.fraud.fraud_rate > 10 ? 'var(--danger)' : 'var(--accent2)' }}>
                  {data.fraud.fraud_rate}%
                </div>
              </div>
              <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--surface2)' }}>
                <div className="h-full rounded-full" style={{ width: `${Math.min(data.fraud.fraud_rate, 100)}%`, background: data.fraud.fraud_rate > 10 ? 'var(--danger)' : 'var(--accent2)' }} />
              </div>
              <div className="text-sm" style={{ color: 'var(--text2)' }}>{data.fraud.fraudulent_docs} / {data.overview.total_documents} docs</div>
            </div>
          </div>
        </Panel>

        {/* Charts row 1 */}
        <div className="grid grid-cols-3 gap-4">
          {/* By Type */}
          <Panel title="Repartition par type">
            <div className="p-4 flex justify-center">
              {typeData.length === 0 ? <p className="text-sm py-8" style={{ color: 'var(--text2)' }}>Aucune donnee</p> : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={typeData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={11}>
                      {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>

          {/* By Zone */}
          <Panel title="Repartition par zone">
            <div className="p-4 flex justify-center">
              {zoneData.length === 0 ? <p className="text-sm py-8" style={{ color: 'var(--text2)' }}>Aucune donnee</p> : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={zoneData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={11}>
                      <Cell fill="#9a6b38" />
                      <Cell fill="#6b7084" />
                      <Cell fill="#b8860b" />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>

          {/* Anomalies by severity */}
          <Panel title="Anomalies par severite">
            <div className="p-4 flex justify-center">
              {anomSevData.length === 0 ? <p className="text-sm py-8" style={{ color: 'var(--text2)' }}>Aucune anomalie</p> : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={anomSevData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={11}>
                      {anomSevData.map((entry) => {
                        const c = entry.name === 'critique' ? '#e03131' : entry.name === 'elevee' ? '#e67700' : entry.name === 'moyenne' ? '#e8a500' : '#5c7cfa'
                        return <Cell key={entry.name} fill={c} />
                      })}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>
        </div>

        {/* Charts row 2 */}
        <div className="grid grid-cols-2 gap-4">
          {/* Pipeline performance */}
          <Panel title="Temps moyen pipeline (ms)">
            <div className="p-4">
              {pipelineData.length === 0 ? <p className="text-sm py-8 text-center" style={{ color: 'var(--text2)' }}>Aucune donnee pipeline</p> : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={pipelineData} layout="vertical" margin={{ left: 80 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7084' }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6b7084' }} width={80} />
                    <Tooltip formatter={(v) => `${v} ms`} />
                    <Bar dataKey="ms" fill="#3b5bdb" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>

          {/* Anomalies by type */}
          <Panel title="Anomalies par type">
            <div className="p-4">
              {anomTypeData.length === 0 ? <p className="text-sm py-8 text-center" style={{ color: 'var(--text2)' }}>Aucune anomalie</p> : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={anomTypeData} layout="vertical" margin={{ left: 120 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7084' }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6b7084' }} width={120} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#e67700" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>
        </div>

        {/* Suppliers summary */}
        <Panel title="Fournisseurs">
          <div className="p-5 grid grid-cols-3 gap-4">
            <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Total fournisseurs</div>
              <div className="text-2xl font-bold">{data.suppliers.total}</div>
            </div>
            <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Score conformite moyen</div>
              <div className="text-2xl font-bold" style={{ color: data.suppliers.avg_conformity > 80 ? 'var(--accent2)' : 'var(--warn)' }}>
                {data.suppliers.avg_conformity}%
              </div>
            </div>
            <div className="rounded-lg p-4" style={{ background: 'var(--bg)' }}>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--text2)' }}>Blacklistes</div>
              <div className="text-2xl font-bold" style={{ color: data.suppliers.blacklisted > 0 ? 'var(--danger)' : 'var(--accent2)' }}>
                {data.suppliers.blacklisted}
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}
