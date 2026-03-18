import React, { useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { Building2, ShieldAlert, Menu, X } from 'lucide-react'

import CRMPage        from './pages/CRMPage'
import CompliancePage from './pages/CompliancePage'

const NAV = [
  { to: '/',           icon: Building2,  label: 'CRM Fournisseurs' },
  { to: '/conformite', icon: ShieldAlert, label: 'Conformité'      },
]

export default function App() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex min-h-screen">
      <aside className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}
             style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3 px-4 py-6 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))' }}>
            <span className="text-white font-bold text-sm">DF</span>
          </div>
          {!collapsed && (
            <div>
              <div className="font-display font-bold text-lg" style={{ color: 'var(--text)' }}>DocuFlow</div>
              <div className="font-mono text-xs" style={{ color: 'var(--text2)' }}>v2.0</div>
            </div>
          )}
          <button className="ml-auto p-1 rounded" onClick={() => setCollapsed(!collapsed)} style={{ color: 'var(--text2)' }}>
            {collapsed ? <Menu size={16} /> : <X size={16} />}
          </button>
        </div>
        <nav className="flex-1 py-4 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all text-sm font-medium ${isActive ? 'text-white' : 'hover:bg-white/5'}`
              }
              style={({ isActive }) => isActive
                ? { background: 'var(--accent)', color: 'white' }
                : { color: 'var(--text2)' }
              }>
              <Icon size={17} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
        {!collapsed && (
          <div className="px-4 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--accent2)' }}>
              <span className="w-2 h-2 rounded-full pulse" style={{ background: 'var(--accent2)' }} />
              Pipeline actif
            </div>
          </div>
        )}
      </aside>
      <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-16' : 'ml-64'}`}>
        <Routes>
          <Route path="/"          element={<CRMPage />} />
          <Route path="/conformite" element={<CompliancePage />} />
        </Routes>
      </main>
    </div>
  )
}
