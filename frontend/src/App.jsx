import React, { useState } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Upload, FileText, Building2,
  ShieldAlert, Database, GitBranch, Menu, X
} from 'lucide-react'

import Dashboard    from './pages/Dashboard'
import UploadPage   from './pages/UploadPage'
import DocumentsPage from './pages/DocumentsPage'
import SuppliersPage from './pages/SuppliersPage'
import CompliancePage from './pages/CompliancePage'
import DataLakePage  from './pages/DataLakePage'
import PipelinePage  from './pages/PipelinePage'

const NAV = [
  { to: '/',           icon: LayoutDashboard, label: 'Dashboard'   },
  { to: '/upload',     icon: Upload,          label: 'Upload'       },
  { to: '/documents',  icon: FileText,        label: 'Documents'    },
  { to: '/suppliers',  icon: Building2,       label: 'Fournisseurs' },
  { to: '/compliance', icon: ShieldAlert,     label: 'Conformité'   },
  { to: '/datalake',   icon: Database,        label: 'Data Lake'    },
  { to: '/pipeline',   icon: GitBranch,       label: 'Pipeline'     },
]

export default function App() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <div className="flex min-h-screen">
      {/* SIDEBAR */}
      <aside className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}
             style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>

        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-6 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))' }}>
            <span className="text-white font-bold text-sm">DF</span>
          </div>
          {!collapsed && (
            <div>
              <div className="font-display font-bold text-lg" style={{ color: 'var(--text)' }}>DocuFlow</div>
              <div className="font-mono text-xs" style={{ color: 'var(--text2)' }}>v2.0 · Hackathon 2026</div>
            </div>
          )}
          <button className="ml-auto p-1 rounded hover:bg-surface-2 transition-colors"
                  onClick={() => setCollapsed(!collapsed)} style={{ color: 'var(--text2)' }}>
            {collapsed ? <Menu size={16} /> : <X size={16} />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all text-sm font-medium
                 ${isActive
                   ? 'text-white'
                   : 'hover:bg-white/5'}`
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

        {/* Status */}
        {!collapsed && (
          <div className="px-4 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--accent2)' }}>
              <span className="w-2 h-2 rounded-full pulse" style={{ background: 'var(--accent2)' }} />
              API connectée
            </div>
          </div>
        )}
      </aside>

      {/* MAIN */}
      <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-16' : 'ml-64'}`}>
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/upload"     element={<UploadPage />} />
          <Route path="/documents"  element={<DocumentsPage />} />
          <Route path="/suppliers"  element={<SuppliersPage />} />
          <Route path="/compliance" element={<CompliancePage />} />
          <Route path="/datalake"   element={<DataLakePage />} />
          <Route path="/pipeline"   element={<PipelinePage />} />
        </Routes>
      </main>
    </div>
  )
}
