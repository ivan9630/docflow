import React, { useState, useEffect } from 'react'
import { triggerDAG, dagStatus } from '../api'
import { Panel, Btn } from '../components/UI'
import toast from 'react-hot-toast'

const DAG_STEPS = [
  { id:'check_pending',       label:'Check Pending',       icon:'🔎', desc:'Vérifie les documents en attente de traitement' },
  { id:'trigger_ocr',         label:'Trigger OCR',         icon:'🔍', desc:'Lance le pipeline OCR + extraction entités' },
  { id:'inter_doc_coherence', label:'Cohérence Inter-docs', icon:'🔗', desc:'Détecte les incohérences entre documents' },
  { id:'autofill_crm',        label:'Auto-fill CRM',       icon:'🏢', desc:'Met à jour les fiches fournisseurs' },
  { id:'autofill_compliance', label:'Auto-fill Conformité', icon:'🔒', desc:'Actualise les scores de conformité' },
  { id:'send_alerts',         label:'Alertes',             icon:'🚨', desc:'Envoie les alertes critiques' },
  { id:'cleanup_logs',        label:'Cleanup',             icon:'🧹', desc:'Nettoyage des logs anciens' },
]

export default function PipelinePage() {
  const [status, setStatus] = useState(null)
  const [running, setRunning] = useState(false)
  const [activeStep, setActiveStep] = useState(null)

  useEffect(() => {
    dagStatus('docuflow_pipeline').then(r => setStatus(r.data)).catch(() => {})
  }, [])

  const handleTrigger = async () => {
    setRunning(true)
    try {
      const r = await triggerDAG('docuflow_pipeline')
      toast.success('DAG Airflow déclenché avec succès !')
      // Simulate progression for demo
      for (let i = 0; i < DAG_STEPS.length; i++) {
        setActiveStep(i)
        await new Promise(res => setTimeout(res, 800))
      }
      setActiveStep(null)
      toast.success('Pipeline terminé !')
    } catch {
      toast.error('Airflow non disponible — pipeline Celery actif')
    } finally { setRunning(false) }
  }

  return (
    <div>
      <div className="pt-8 px-8 mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Pipeline Orchestration</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>
            DAG Airflow — docuflow_pipeline · Schedule: toutes les 5 min
          </p>
        </div>
        <Btn variant="primary" onClick={handleTrigger} disabled={running}>
          {running ? '⚙️ En cours…' : '▶ Déclencher le DAG'}
        </Btn>
      </div>

      <div className="px-8 space-y-6">
        {/* Status Airflow */}
        <div className="rounded-xl p-4 flex items-center gap-4"
             style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div className="text-3xl">🌊</div>
          <div>
            <div className="font-display font-bold">Apache Airflow</div>
            <div className="text-sm" style={{ color: 'var(--text2)' }}>
              {status?.error ? '⚠️ Non disponible (pipeline Celery actif en remplacement)'
                             : `✅ Connecté — DAG: ${status?.dag_id || 'docuflow_pipeline'}`}
            </div>
          </div>
          <div className="ml-auto">
            <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer">
              <Btn variant="ghost" size="sm">Ouvrir Airflow UI →</Btn>
            </a>
          </div>
        </div>

        {/* DAG Visualisation */}
        <Panel title="DAG — docuflow_pipeline">
          <div className="p-6">
            {/* Linear flow */}
            <div className="flex flex-col gap-3">
              {DAG_STEPS.map((step, i) => (
                <div key={step.id} className="flex items-start gap-4">
                  {/* Connector */}
                  <div className="flex flex-col items-center">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0 transition-all"
                         style={{
                           background: activeStep === i ? 'var(--accent)' :
                                       activeStep !== null && i < activeStep ? 'rgba(0,212,170,0.2)' : 'var(--surface2)',
                           border: `2px solid ${activeStep === i ? 'var(--accent)' :
                                                activeStep !== null && i < activeStep ? 'var(--accent2)' : 'var(--border)'}`,
                         }}>
                      {activeStep !== null && i < activeStep ? '✓' : step.icon}
                    </div>
                    {i < DAG_STEPS.length - 1 && (
                      <div className="w-0.5 h-6 mt-1"
                           style={{ background: activeStep !== null && i < activeStep ? 'var(--accent2)' : 'var(--border)' }} />
                    )}
                  </div>
                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="font-display font-bold text-sm"
                           style={{ color: activeStep === i ? 'var(--accent)' : 'var(--text)' }}>
                        {step.label}
                      </div>
                      {activeStep === i && (
                        <span className="font-mono text-xs px-2 py-0.5 rounded animate-pulse"
                              style={{ background: 'rgba(108,99,255,0.15)', color: 'var(--accent)' }}>
                          En cours…
                        </span>
                      )}
                      {activeStep !== null && i < activeStep && (
                        <span className="font-mono text-xs" style={{ color: 'var(--accent2)' }}>✓ Terminé</span>
                      )}
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: 'var(--text2)' }}>{step.desc}</div>
                    {/* Task ID */}
                    <div className="font-mono text-xs mt-1" style={{ color: 'var(--border)' }}>task_id: {step.id}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Parallel branches */}
            <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="text-xs mb-2" style={{ color: 'var(--text2)' }}>
                ↳ Les tâches <strong>autofill_crm</strong> et <strong>autofill_compliance</strong> s'exécutent en parallèle
              </div>
              <div className="flex gap-2 items-center">
                <div className="px-3 py-1.5 rounded-lg text-xs font-mono" style={{ background: 'var(--surface2)', border: '1px solid var(--border)' }}>
                  inter_doc_coherence
                </div>
                <span style={{ color: 'var(--accent)' }}>→</span>
                <div className="flex flex-col gap-1">
                  <div className="px-3 py-1.5 rounded-lg text-xs font-mono" style={{ background: 'rgba(108,99,255,0.1)', border: '1px solid var(--accent)' }}>
                    autofill_crm
                  </div>
                  <div className="px-3 py-1.5 rounded-lg text-xs font-mono" style={{ background: 'rgba(0,212,170,0.1)', border: '1px solid var(--accent2)' }}>
                    autofill_compliance
                  </div>
                </div>
                <span style={{ color: 'var(--accent)' }}>→</span>
                <div className="px-3 py-1.5 rounded-lg text-xs font-mono" style={{ background: 'var(--surface2)', border: '1px solid var(--border)' }}>
                  send_alerts
                </div>
              </div>
            </div>
          </div>
        </Panel>

        {/* Access links */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label:'Airflow UI',    url:'http://localhost:8080', icon:'🌊', user:'admin / docuflow123' },
            { label:'Flower (Celery)',url:'http://localhost:5555', icon:'🌸', user:'Monitoring workers' },
            { label:'MinIO Console', url:'http://localhost:9001', icon:'💾', user:'docuflow / docuflow123' },
          ].map(({ label, url, icon, user }) => (
            <a key={label} href={url} target="_blank" rel="noopener noreferrer"
               className="rounded-xl p-4 block transition-all hover:scale-[1.02]"
               style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
              <div className="text-2xl mb-2">{icon}</div>
              <div className="font-display font-bold text-sm">{label}</div>
              <div className="font-mono text-xs mt-1" style={{ color: 'var(--accent)' }}>{url}</div>
              <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>{user}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
