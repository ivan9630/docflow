import React from 'react'

// ── Panel ─────────────────────────────────────────────────────────
export function Panel({ title, children, action, className = '' }) {
  return (
    <div className={`rounded-xl overflow-hidden shadow-sm ${className}`}
         style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      {title && (
        <div className="flex items-center justify-between px-5 py-3 border-b"
             style={{ borderColor: 'var(--border)' }}>
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</span>
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
    uploade:       ['var(--gold)',    'rgba(232,165,0,0.1)'],
    en_traitement: ['var(--accent)',  'rgba(59,91,219,0.1)'],
    ocr_ok:        ['var(--accent)',  'rgba(59,91,219,0.1)'],
    extrait:       ['var(--accent2)', 'rgba(12,166,120,0.1)'],
    verifie:       ['var(--accent2)', 'rgba(12,166,120,0.1)'],
    valide:        ['var(--accent2)', 'rgba(12,166,120,0.1)'],
    anomalie:      ['var(--warn)',    'rgba(230,119,0,0.1)'],
    rejete:        ['var(--danger)',  'rgba(224,49,49,0.1)'],
  }
  const [color, bg] = map[status] || ['var(--text2)', 'rgba(0,0,0,0.04)']
  const labels = {
    uploade:'Upload', en_traitement:'En cours', ocr_ok:'OCR OK',
    extrait:'Extrait', verifie:'Verifie', valide:'Valide',
    anomalie:'Anomalie', rejete:'Rejete'
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
          style={{ color, background: bg }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      {labels[status] || status}
    </span>
  )
}

// ── Type Badge ────────────────────────────────────────────────────
export function TypeBadge({ type }) {
  const labels = {
    facture:'Facture', devis:'Devis', bon_commande:'Bon Cmd',
    attestation_urssaf:'URSSAF', attestation_fiscale:'Fiscal',
    attestation_siret:'SIRET', kbis:'KBIS', rib:'RIB',
    contrat:'Contrat', avoir:'Avoir', note_frais:'Note frais', autre:'Autre'
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
          style={{ background: 'var(--surface2)', color: 'var(--text2)' }}>
      {labels[type] || type || '—'}
    </span>
  )
}

// ── Zone Badge ────────────────────────────────────────────────────
export function ZoneBadge({ zone }) {
  const map = {
    raw:     ['#9a6b38', 'rgba(154,107,56,0.1)'],
    clean:   ['#6b7084', 'rgba(107,112,132,0.1)'],
    curated: ['#b8860b', 'rgba(184,134,11,0.1)'],
  }
  const [color, bg] = map[zone] || ['var(--text2)', 'transparent']
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase"
          style={{ color, background: bg }}>
      {zone}
    </span>
  )
}

// ── Button ────────────────────────────────────────────────────────
export function Btn({ children, onClick, variant = 'primary', size = 'md', disabled = false, className = '' }) {
  const variants = {
    primary:   { background: 'var(--accent)',   color: 'white', border: 'none' },
    success:   { background: 'var(--accent2)',  color: 'white', border: 'none' },
    danger:    { background: 'var(--danger)',   color: 'white', border: 'none' },
    secondary: { background: 'var(--surface2)', color: 'var(--text)', border: '1px solid var(--border)' },
    ghost:     { background: 'transparent',     color: 'var(--text2)', border: '1px solid var(--border)' },
  }
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2 text-sm', lg: 'px-6 py-3 text-base' }
  return (
    <button onClick={onClick} disabled={disabled}
      className={`rounded-lg font-medium transition-all hover:opacity-80 active:scale-[0.98] disabled:opacity-40 ${sizes[size]} ${className}`}
      style={variants[variant]}>
      {children}
    </button>
  )
}

// ── Loading Spinner ───────────────────────────────────────────────
export function Spinner({ size = 20 }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="rounded-full animate-spin border-2 border-t-transparent"
           style={{ width: size, height: size, borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────
export function Empty({ title = 'Aucune donnee', sub = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="font-semibold text-base" style={{ color: 'var(--text)' }}>{title}</div>
      {sub && <div className="text-sm mt-1" style={{ color: 'var(--text2)' }}>{sub}</div>}
    </div>
  )
}

// ── Severity Badge ────────────────────────────────────────────────
export function SeverityBadge({ sev }) {
  const map = {
    critique: ['var(--danger)', 'rgba(224,49,49,0.1)'],
    elevee:   ['var(--warn)',   'rgba(230,119,0,0.1)'],
    moyenne:  ['var(--gold)',   'rgba(232,165,0,0.1)'],
    faible:   ['#5c7cfa',      'rgba(92,124,250,0.1)'],
  }
  const [color, bg] = map[sev] || ['var(--text2)', 'transparent']
  return (
    <span className="px-2 py-0.5 rounded-full text-xs font-medium uppercase"
          style={{ color, background: bg }}>{sev}</span>
  )
}

// ── Fraud Score ───────────────────────────────────────────────────
export function FraudScore({ score = 0 }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct > 60 ? 'var(--danger)' : pct > 30 ? 'var(--warn)' : 'var(--accent2)'
  return <span className="text-xs font-semibold" style={{ color }}>{pct}%</span>
}

// ── Table ─────────────────────────────────────────────────────────
export function Table({ headers, children, className = '' }) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-collapse">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {headers.map(h => (
              <th key={h} className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wide"
                  style={{ color: 'var(--text2)' }}>{h}</th>
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
    <tr onClick={onClick} className="transition-colors hover:bg-gray-50"
        style={{ borderBottom: '1px solid var(--border)', cursor: onClick ? 'pointer' : 'default' }}>
      {children}
    </tr>
  )
}

export function Td({ children, className = '' }) {
  return <td className={`px-4 py-3 text-sm ${className}`}>{children}</td>
}

// ── KPI Card ──────────────────────────────────────────────────────
export function KpiCard({ label, value, color = 'accent' }) {
  const colors = {
    accent:  'var(--accent)',
    success: 'var(--accent2)',
    warning: 'var(--warn)',
    danger:  'var(--danger)',
    gold:    'var(--gold)',
  }
  const c = colors[color] || colors.accent
  return (
    <div className="rounded-xl p-4 shadow-sm"
         style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--text2)' }}>{label}</div>
      <div className="text-2xl font-bold" style={{ color: c }}>{value ?? '—'}</div>
    </div>
  )
}

// ── Page Header ───────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex items-start justify-between mb-6 pt-8 px-8">
      <div>
        <h1 className="text-xl font-bold">{title}</h1>
        {subtitle && <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}
