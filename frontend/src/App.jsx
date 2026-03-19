import React, { useState } from 'react'
import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { Building2, ShieldAlert, BarChart3, LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAuth } from './context/AuthContext'

import LoginPage      from './pages/LoginPage'
import CRMPage        from './pages/CRMPage'
import CompliancePage from './pages/CompliancePage'
import AdminPage      from './pages/AdminPage'

const ROLE_LABELS = { admin: 'Admin', gestionnaire: 'Gestionnaire', conformite: 'Conformite' }
const ROLE_COLORS = { admin: '#4f6ef7', gestionnaire: '#10b981', conformite: '#8b5cf6' }

function ProtectedRoute({ children, roles }) {
  const { user, loading, hasRole } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (roles && !hasRole(...roles)) return <Navigate to="/" replace />
  return children
}

export default function App() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout, hasRole } = useAuth()
  const navigate = useNavigate()

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  const NAV = [
    hasRole('gestionnaire') && { to: '/',           icon: Building2,   label: 'CRM Fournisseurs' },
    hasRole('conformite')   && { to: '/conformite', icon: ShieldAlert, label: 'Conformite'       },
    user.role === 'admin'   && { to: '/admin',      icon: BarChart3,   label: 'Monitoring'       },
  ].filter(Boolean)

  const defaultRoute = user.role === 'admin' ? '/admin' : user.role === 'conformite' ? '/conformite' : '/'
  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="flex min-h-screen">
      <aside className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-200 ${collapsed ? 'w-[60px]' : 'w-[220px]'}`}
             style={{ background: 'var(--surface)', borderRight: '1px solid var(--border-light)', boxShadow: '1px 0 3px rgba(0,0,0,0.03)' }}>

        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 h-[60px] flex-shrink-0" style={{ borderBottom: '1px solid var(--border-light)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ background: 'var(--accent)', boxShadow: '0 2px 4px rgba(79,110,247,0.25)' }}>
            <span className="text-white font-bold text-sm">DF</span>
          </div>
          {!collapsed && <span className="font-bold text-[15px]" style={{ color: 'var(--text)' }}>DocuFlow</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2.5 overflow-y-auto">
          {!collapsed && <div className="text-[10px] font-semibold uppercase tracking-widest px-2.5 mb-2" style={{ color: 'var(--text3)' }}>Navigation</div>}
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-2.5 py-2 rounded-lg mb-0.5 transition-all text-[13px] font-medium ${isActive ? '' : 'hover:bg-[#f5f6f8]'}`
              }
              style={({ isActive }) => isActive
                ? { background: 'var(--accent-light)', color: 'var(--accent)', fontWeight: 600 }
                : { color: 'var(--text2)' }
              }>
              <Icon size={17} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-2.5 py-3 flex-shrink-0" style={{ borderTop: '1px solid var(--border-light)' }}>
          {!collapsed && (
            <div className="flex items-center gap-2 mb-2.5 px-1">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-[11px] font-bold text-white"
                   style={{ background: ROLE_COLORS[user.role] || 'var(--accent)' }}>
                {user.nom_complet?.[0]?.toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[12px] font-semibold truncate">{user.nom_complet}</div>
                <div className="text-[11px] truncate" style={{ color: 'var(--text3)' }}>{ROLE_LABELS[user.role]}</div>
              </div>
            </div>
          )}
          <div className="flex gap-1">
            <button onClick={handleLogout}
                    className="flex items-center gap-1.5 flex-1 px-2.5 py-1.5 rounded-lg text-[12px] font-medium transition-all hover:bg-[#f5f6f8]"
                    style={{ color: 'var(--text3)' }}>
              <LogOut size={13} />
              {!collapsed && <span>Deconnexion</span>}
            </button>
            <button onClick={() => setCollapsed(!collapsed)}
                    className="p-1.5 rounded-lg hover:bg-[#f5f6f8] transition-all"
                    style={{ color: 'var(--text3)' }}>
              {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
            </button>
          </div>
        </div>
      </aside>

      <main className={`flex-1 transition-all duration-200 ${collapsed ? 'ml-[60px]' : 'ml-[220px]'}`}
            style={{ background: 'var(--bg)' }}>
        <Routes>
          <Route path="/login" element={<Navigate to={defaultRoute} replace />} />
          <Route path="/" element={<ProtectedRoute roles={['gestionnaire']}><CRMPage /></ProtectedRoute>} />
          <Route path="/conformite" element={<ProtectedRoute roles={['conformite']}><CompliancePage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to={defaultRoute} replace />} />
        </Routes>
      </main>
    </div>
  )
}
