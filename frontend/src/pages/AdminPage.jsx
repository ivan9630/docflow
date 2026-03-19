import React, { useState, useEffect } from 'react'
import { adminStats } from '../api'
import { Panel, Spinner, KpiCard } from '../components/UI'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'

const COLORS = ['#4f6ef7', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16']
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
  const pipelineData = Object.entries(data.pipeline.avg_time_ms).map(([k, v]) => ({ name: k, ms: v }))
  const anomSevData = Object.entries(data.anomalies.by_severity || {}).map(([k, v]) => ({ name: k, value: v }))
  const anomTypeData = Object.entries(data.anomalies.by_type || {}).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))

  const tooltipStyle = { contentStyle: { background: 'var(--surface)', border: '1px solid var(--border-light)', borderRadius: 8, fontSize: 12, boxShadow: 'var(--shadow-md)' } }

  return (
    <div className="fade-in">
      <div className="pt-8 px-8 mb-6">
        <h1 className="text-lg font-bold">Monitoring</h1>
        <p className="text-[13px] mt-0.5" style={{ color: 'var(--text2)' }}>Vue d'ensemble du systeme DocuFlow</p>
      </div>

      <div className="px-8 pb-8 space-y-5">
        {/* KPIs */}
        <div className="grid grid-cols-5 gap-3">
          <KpiCard label="Documents" value={data.overview.total_documents} color="accent" />
          <KpiCard label="Fournisseurs" value={data.overview.total_suppliers} color="success" />
          <KpiCard label="Utilisateurs" value={data.overview.total_users} color="accent" />
          <KpiCard label="Anomalies" value={data.anomalies.open} color="warning" />
          <KpiCard label="Total facture" value={`${data.overview.total_invoiced.toLocaleString()} EUR`} color="gold" />
        </div>

        {/* AI Quality */}
        <Panel title="Qualite IA">
          <div className="p-5">
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Modele', value: data.ai_quality.classifier_model, sub: `${data.ai_quality.training_samples} samples`, color: 'var(--text)' },
                { label: 'Accuracy', value: `${data.ai_quality.classifier_accuracy}%`, sub: `${data.ai_quality.classes} classes`, color: 'var(--accent2)' },
                { label: 'Confiance OCR', value: `${data.ai_quality.avg_ocr_confidence}%`, sub: 'moyenne', color: data.ai_quality.avg_ocr_confidence > 80 ? 'var(--accent2)' : 'var(--warn)' },
                { label: 'Confiance classif.', value: `${data.ai_quality.avg_classification_confidence}%`, sub: 'moyenne', color: data.ai_quality.avg_classification_confidence > 80 ? 'var(--accent2)' : 'var(--warn)' },
              ].map((item, i) => (
                <div key={i} className="rounded-lg p-4" style={{ background: 'var(--surface2)', border: '1px solid var(--border-light)' }}>
                  <div className="text-[11px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text3)' }}>{item.label}</div>
                  <div className="text-xl font-bold" style={{ color: item.color }}>{item.value}</div>
                  <div className="text-[11px] mt-0.5" style={{ color: 'var(--text3)' }}>{item.sub}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-4 rounded-lg p-4" style={{ background: 'var(--surface2)', border: '1px solid var(--border-light)' }}>
              <div className="min-w-[120px]">
                <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Taux de fraude</div>
                <div className="text-xl font-bold" style={{ color: data.fraud.fraud_rate > 10 ? 'var(--danger)' : 'var(--accent2)' }}>{data.fraud.fraud_rate}%</div>
              </div>
              <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--border-light)' }}>
                <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(data.fraud.fraud_rate, 100)}%`, background: data.fraud.fraud_rate > 10 ? 'var(--danger)' : 'var(--accent2)' }} />
              </div>
              <div className="text-[12px] font-medium" style={{ color: 'var(--text2)' }}>{data.fraud.fraudulent_docs} / {data.overview.total_documents}</div>
            </div>
          </div>
        </Panel>

        {/* Charts row 1 */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { title: 'Par type', data: typeData, colors: COLORS },
            { title: 'Par zone', data: zoneData, colors: ['#92400e', '#6b7280', '#d97706'] },
            { title: 'Anomalies / severite', data: anomSevData, colors: null },
          ].map(({ title, data: chartData, colors }, idx) => (
            <Panel key={idx} title={title}>
              <div className="p-4 flex justify-center">
                {chartData.length === 0 ? <p className="text-[13px] py-10" style={{ color: 'var(--text3)' }}>Aucune donnee</p> : (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={chartData} cx="50%" cy="50%" outerRadius={72} innerRadius={35} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={10} strokeWidth={2} stroke="var(--surface)">
                        {chartData.map((entry, i) => {
                          const sevColors = { critique: '#ef4444', elevee: '#f59e0b', moyenne: '#d97706', faible: '#6366f1' }
                          const fill = colors ? colors[i % colors.length] : (sevColors[entry.name] || '#6b7280')
                          return <Cell key={i} fill={fill} />
                        })}
                      </Pie>
                      <Tooltip {...tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Panel>
          ))}
        </div>

        {/* Charts row 2 */}
        <div className="grid grid-cols-2 gap-4">
          <Panel title="Temps pipeline (ms)">
            <div className="p-4">
              {pipelineData.length === 0 ? <p className="text-[13px] py-10 text-center" style={{ color: 'var(--text3)' }}>Aucune donnee</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={pipelineData} layout="vertical" margin={{ left: 70 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} width={70} axisLine={false} tickLine={false} />
                    <Tooltip {...tooltipStyle} formatter={(v) => `${v} ms`} />
                    <Bar dataKey="ms" fill="var(--accent)" radius={[0, 6, 6, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>
          <Panel title="Anomalies par type">
            <div className="p-4">
              {anomTypeData.length === 0 ? <p className="text-[13px] py-10 text-center" style={{ color: 'var(--text3)' }}>Aucune anomalie</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={anomTypeData} layout="vertical" margin={{ left: 110 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#6b7280' }} width={110} axisLine={false} tickLine={false} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="value" fill="var(--warn)" radius={[0, 6, 6, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Panel>
        </div>

        {/* Suppliers */}
        <Panel title="Fournisseurs">
          <div className="p-5 grid grid-cols-3 gap-3">
            {[
              { label: 'Total', value: data.suppliers.total, color: 'var(--text)' },
              { label: 'Conformite moyenne', value: `${data.suppliers.avg_conformity}%`, color: data.suppliers.avg_conformity > 80 ? 'var(--accent2)' : 'var(--warn)' },
              { label: 'Blacklistes', value: data.suppliers.blacklisted, color: data.suppliers.blacklisted > 0 ? 'var(--danger)' : 'var(--accent2)' },
            ].map((item, i) => (
              <div key={i} className="rounded-lg p-4" style={{ background: 'var(--surface2)', border: '1px solid var(--border-light)' }}>
                <div className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>{item.label}</div>
                <div className="text-xl font-bold" style={{ color: item.color }}>{item.value}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}
