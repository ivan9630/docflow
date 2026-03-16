import React from 'react'

// ── KPI Card ──────────────────────────────────────────────────────
export function KpiCard({ label, value, delta, color = 'accent', icon }) {
  const colors = {
    accent:  'var(--accent)',
    success: 'var(--accent2)',
    warning: 'var(--warn)',
    danger:  'var(--danger)',
    gold:    'var(--gold)',
  }
  const c = colors[color] || colors.accent
  return (
    <div className="rounded-xl p-5 relative overflow-hidden slide-in"
         style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="absolute top-0 left-0 right-0 h-0.5" style={{ background: c }} />
      <div className="font-mono text-xs uppercase tracking-widest mb-2" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="font-display text-3xl font-bold" style={{ color: c }}>{value ?? '—'}</div>
      {delta && <div className="text-xs mt-1" style={{ color: 'var(--text2)' }}>{delta}</div>}
    </div>
  )
}

// ── Page Header ───────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex items-start justify-between mb-8 pt-8 px-8">
      <div>
        <h1 className="font-display text-2xl font-bold">{title}</h1>
        {subtitle && <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-3">{actions}</div>}
    </div>
  )
}

// ── Panel ─────────────────────────────────────────────────────────
export function Panel({ title, children, action, className = '' }) {
  return (
    <div className={`rounded-xl overflow-hidden ${className}`}
         style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      {title && (
        <div className="flex items-center justify-between px-5 py-3 border-b"
             style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <span className="font-display text-sm font-bold uppercase tracking-wide">{title}</span>
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

// ── Status Pill ───────────────────────────────────────────────────
export function StatusPill({ status }) {
  const map = {
    uploade:       ['📤', 'var(--gold)',    'rgba(255,209,102,0.12)'],
    en_traitement: ['⚙️', 'var(--accent)',  'rgba(108,99,255,0.12)'],
    ocr_ok:        ['🔍', 'var(--accent)',  'rgba(108,99,255,0.12)'],
    extrait:       ['📊', 'var(--accent2)', 'rgba(0,212,170,0.12)'],
    verifie:       ['✅', 'var(--accent2)', 'rgba(0,212,170,0.12)'],
    valide:        ['✓',  'var(--accent2)', 'rgba(0,212,170,0.12)'],
    anomalie:      ['⚠️', 'var(--warn)',    'rgba(255,107,53,0.12)'],
    rejete:        ['✗',  'var(--danger)',  'rgba(255,51,102,0.12)'],
  }
  const [icon, color, bg] = map[status] || ['?', 'var(--text2)', 'rgba(255,255,255,0.05)']
  const labels = {
    uploade:'Uploadé', en_traitement:'En cours', ocr_ok:'OCR OK',
    extrait:'Extrait', verifie:'Vérifié', valide:'Validé',
    anomalie:'Anomalie', rejete:'Rejeté'
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-xs font-bold"
          style={{ color, background: bg }}>
      {icon} {labels[status] || status}
    </span>
  )
}

// ── Type Badge ────────────────────────────────────────────────────
export function TypeBadge({ type }) {
  const map = {
    facture:'🧾', devis:'📋', bon_commande:'📦', attestation_urssaf:'✅',
    attestation_fiscale:'📑', kbis:'🏢', rib:'🏦', contrat:'📝', autre:'📄'
  }
  const labels = {
    facture:'Facture', devis:'Devis', bon_commande:'Bon Cmd',
    attestation_urssaf:'URSSAF', attestation_fiscale:'Fiscal',
    kbis:'KBIS', rib:'RIB', contrat:'Contrat', autre:'Autre'
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium"
          style={{ background: 'var(--surface2)', color: 'var(--text2)', border: '1px solid var(--border)' }}>
      {map[type] || '📄'} {labels[type] || type || '?'}
    </span>
  )
}

// ── Zone Badge ────────────────────────────────────────────────────
export function ZoneBadge({ zone }) {
  const map = {
    raw:     ['🟤','#cd7f32','rgba(205,127,50,0.15)'],
    clean:   ['⚪','#c0c0c0','rgba(192,192,192,0.15)'],
    curated: ['🟡','#ffd700','rgba(255,215,0,0.15)'],
  }
  const [icon, color, bg] = map[zone] || ['?','var(--text2)','transparent']
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-xs font-bold uppercase"
          style={{ color, background: bg }}>
      {icon} {zone}
    </span>
  )
}

// ── Fraud Score ───────────────────────────────────────────────────
export function FraudScore({ score = 0 }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct > 60 ? 'var(--danger)' : pct > 30 ? 'var(--warn)' : 'var(--accent2)'
  return (
    <span className="font-mono text-xs font-bold" style={{ color }}>{pct}%</span>
  )
}

// ── Button ────────────────────────────────────────────────────────
export function Btn({ children, onClick, variant = 'primary', size = 'md', disabled = false, className = '' }) {
  const variants = {
    primary:   { background: 'var(--accent)',  color: 'white', border: 'none' },
    success:   { background: 'var(--accent2)', color: 'white', border: 'none' },
    danger:    { background: 'var(--danger)',  color: 'white', border: 'none' },
    secondary: { background: 'var(--surface2)',color: 'var(--text)', border: '1px solid var(--border)' },
    ghost:     { background: 'transparent',    color: 'var(--text2)', border: '1px solid var(--border)' },
  }
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2 text-sm', lg: 'px-6 py-3 text-base' }
  return (
    <button onClick={onClick} disabled={disabled}
      className={`rounded-lg font-medium transition-all hover:opacity-90 active:scale-95 disabled:opacity-40 ${sizes[size]} ${className}`}
      style={variants[variant]}>
      {children}
    </button>
  )
}

// ── Loading Spinner ───────────────────────────────────────────────
export function Spinner({ size = 24 }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="rounded-full animate-spin border-2 border-t-transparent"
           style={{ width: size, height: size, borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────
export function Empty({ icon = '📭', title = 'Aucune donnée', sub = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-4xl mb-3">{icon}</span>
      <div className="font-display font-bold text-lg">{title}</div>
      {sub && <div className="text-sm mt-1" style={{ color: 'var(--text2)' }}>{sub}</div>}
    </div>
  )
}

// ── Severity Badge ────────────────────────────────────────────────
export function SeverityBadge({ sev }) {
  const map = {
    critique: ['var(--danger)', 'rgba(255,51,102,0.15)'],
    elevee:   ['var(--warn)',   'rgba(255,107,53,0.15)'],
    moyenne:  ['var(--gold)',   'rgba(255,209,102,0.15)'],
    faible:   ['#6699ff',      'rgba(102,153,255,0.15)'],
  }
  const [color, bg] = map[sev] || ['var(--text2)', 'transparent']
  return (
    <span className="px-2 py-0.5 rounded font-mono text-xs font-bold uppercase"
          style={{ color, background: bg }}>{sev}</span>
  )
}

// ── Table ─────────────────────────────────────────────────────────
export function Table({ headers, children, className = '' }) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-collapse">
        <thead>
          <tr style={{ borderBottom: '2px solid var(--border)' }}>
            {headers.map(h => (
              <th key={h} className="text-left px-4 py-3 font-mono text-xs uppercase tracking-widest"
                  style={{ color: 'var(--text2)', background: 'var(--surface)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

export function Tr({ children, onClick }) {
  return (
    <tr onClick={onClick} className="transition-colors"
        style={{ borderBottom: '1px solid var(--border)', cursor: onClick ? 'pointer' : 'default' }}
        onMouseEnter={e => onClick && (e.currentTarget.style.background = 'var(--surface2)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
      {children}
    </tr>
  )
}

export function Td({ children, className = '' }) {
  return <td className={`px-4 py-3 text-sm ${className}`}>{children}</td>
}
