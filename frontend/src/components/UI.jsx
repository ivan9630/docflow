import React from 'react'

// ── Panel ─────────────────────────────────────────────────────────
export function Panel({ title, children, action, className = '' }) {
  return (
    <div className={`rounded-xl overflow-hidden slide-in ${className}`}
         style={{ background: 'var(--surface)', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow)' }}>
      {title && (
        <div className="flex items-center justify-between px-5 py-3.5"
             style={{ borderBottom: '1px solid var(--border-light)' }}>
          <span className="text-[13px] font-semibold tracking-wide" style={{ color: 'var(--text)' }}>{title}</span>
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
    uploade:       ['var(--gold)',    'var(--warn-light)'],
    en_traitement: ['var(--accent)',  'var(--accent-light)'],
    ocr_ok:        ['var(--accent)',  'var(--accent-light)'],
    extrait:       ['var(--accent2)', 'var(--accent2-light)'],
    verifie:       ['var(--accent2)', 'var(--accent2-light)'],
    valide:        ['var(--accent2)', 'var(--accent2-light)'],
    anomalie:      ['var(--warn)',    'var(--warn-light)'],
    rejete:        ['var(--danger)',  'var(--danger-light)'],
  }
  const [color, bg] = map[status] || ['var(--text2)', 'var(--surface2)']
  const labels = {
    uploade:'Upload', en_traitement:'En cours', ocr_ok:'OCR OK',
    extrait:'Extrait', verifie:'Verifie', valide:'Valide',
    anomalie:'Anomalie', rejete:'Rejete'
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold"
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
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium"
          style={{ background: 'var(--surface2)', color: 'var(--text2)', border: '1px solid var(--border-light)' }}>
      {labels[type] || type || '—'}
    </span>
  )
}

// ── Zone Badge ────────────────────────────────────────────────────
export function ZoneBadge({ zone }) {
  const map = {
    raw:     ['#92400e', 'rgba(146,64,14,0.08)'],
    clean:   ['var(--text2)', 'var(--surface2)'],
    curated: ['var(--gold)', 'var(--warn-light)'],
  }
  const [color, bg] = map[zone] || ['var(--text2)', 'transparent']
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold uppercase"
          style={{ color, background: bg }}>
      {zone}
    </span>
  )
}

// ── Button ────────────────────────────────────────────────────────
export function Btn({ children, onClick, variant = 'primary', size = 'md', disabled = false, className = '' }) {
  const base = 'rounded-lg font-medium transition-all active:scale-[0.97] disabled:opacity-40 '
  const variants = {
    primary:   { background: 'var(--accent)', color: 'white', border: 'none', boxShadow: '0 1px 2px rgba(79,110,247,0.3)' },
    success:   { background: 'var(--accent2)', color: 'white', border: 'none' },
    danger:    { background: 'var(--danger)', color: 'white', border: 'none' },
    secondary: { background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' },
    ghost:     { background: 'transparent', color: 'var(--text2)', border: '1px solid var(--border)' },
  }
  const sizes = { sm: 'px-3 py-1.5 text-[12px]', md: 'px-4 py-2 text-[13px]', lg: 'px-5 py-2.5 text-sm' }
  return (
    <button onClick={onClick} disabled={disabled}
      className={`${base} hover:brightness-95 ${sizes[size]} ${className}`}
      style={variants[variant]}>
      {children}
    </button>
  )
}

// ── Loading Spinner ───────────────────────────────────────────────
export function Spinner({ size = 20 }) {
  return (
    <div className="flex items-center justify-center p-10">
      <div className="rounded-full animate-spin border-2 border-t-transparent"
           style={{ width: size, height: size, borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────
export function Empty({ title = 'Aucune donnee', sub = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 px-4 text-center">
      <div className="w-10 h-10 rounded-full flex items-center justify-center mb-3" style={{ background: 'var(--surface2)' }}>
        <span className="text-base" style={{ color: 'var(--text3)' }}>—</span>
      </div>
      <div className="font-medium text-sm" style={{ color: 'var(--text)' }}>{title}</div>
      {sub && <div className="text-[13px] mt-1 max-w-xs" style={{ color: 'var(--text2)' }}>{sub}</div>}
    </div>
  )
}

// ── Severity Badge ────────────────────────────────────────────────
export function SeverityBadge({ sev }) {
  const map = {
    critique: ['var(--danger)', 'var(--danger-light)'],
    elevee:   ['var(--warn)',   'var(--warn-light)'],
    moyenne:  ['var(--gold)',   'var(--warn-light)'],
    faible:   ['#6366f1',      'rgba(99,102,241,0.08)'],
  }
  const [color, bg] = map[sev] || ['var(--text2)', 'transparent']
  return (
    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold capitalize"
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
          <tr>
            {headers.map(h => (
              <th key={h} className="text-left px-5 py-3 text-[11px] font-semibold uppercase tracking-wider"
                  style={{ color: 'var(--text3)', borderBottom: '1px solid var(--border-light)' }}>{h}</th>
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
    <tr onClick={onClick}
        className="transition-colors hover:bg-[#f8f9fb]"
        style={{ borderBottom: '1px solid var(--border-light)', cursor: onClick ? 'pointer' : 'default' }}>
      {children}
    </tr>
  )
}

export function Td({ children, className = '' }) {
  return <td className={`px-5 py-3 text-sm ${className}`}>{children}</td>
}

// ── KPI Card ──────────────────────────────────────────────────────
export function KpiCard({ label, value, color = 'accent' }) {
  const colors = {
    accent:  { main: 'var(--accent)',  bg: 'var(--accent-light)' },
    success: { main: 'var(--accent2)', bg: 'var(--accent2-light)' },
    warning: { main: 'var(--warn)',    bg: 'var(--warn-light)' },
    danger:  { main: 'var(--danger)',  bg: 'var(--danger-light)' },
    gold:    { main: 'var(--gold)',    bg: 'var(--warn-light)' },
  }
  const c = colors[color] || colors.accent
  return (
    <div className="rounded-xl p-5 relative overflow-hidden"
         style={{ background: 'var(--surface)', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow)' }}>
      <div className="absolute top-0 left-0 w-1 h-full rounded-r" style={{ background: c.main }} />
      <div className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text3)' }}>{label}</div>
      <div className="text-2xl font-bold" style={{ color: c.main }}>{value ?? '—'}</div>
    </div>
  )
}

// ── Page Header ───────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex items-start justify-between mb-6 pt-8 px-8">
      <div>
        <h1 className="text-lg font-bold" style={{ color: 'var(--text)' }}>{title}</h1>
        {subtitle && <p className="text-[13px] mt-0.5" style={{ color: 'var(--text2)' }}>{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}
