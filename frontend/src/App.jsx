import React, { useState } from 'react'
import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { Building2, ShieldAlert, BarChart3, LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAuth } from './context/AuthContext'

import LoginPage      from './pages/LoginPage'
import CRMPage        from './pages/CRMPage'
import CompliancePage from './pages/CompliancePage'
import AdminPage      from './pages/AdminPage'

const ROLE_LABELS = { admin: 'Admin', gestionnaire: 'Gestionnaire', conformite: 'Conformite' }

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

  // Redirect admin to /admin by default
  const defaultRoute = user.role === 'admin' ? '/admin' : user.role === 'conformite' ? '/conformite' : '/'

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="flex min-h-screen">
      <aside className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-200 ${collapsed ? 'w-16' : 'w-56'}`}
             style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>

        <div className="flex items-center gap-3 px-4 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ background: 'var(--accent)' }}>
            <span className="text-white font-bold text-sm">DF</span>
          </div>
          {!collapsed && <span className="font-bold text-base" style={{ color: 'var(--text)' }}>DocuFlow</span>}
        </div>

        <nav className="flex-1 py-3 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg mb-0.5 transition-all text-sm font-medium ${isActive ? '' : 'hover:bg-gray-100'}`
              }
              style={({ isActive }) => isActive
                ? { background: 'rgba(59,91,219,0.08)', color: 'var(--accent)' }
                : { color: 'var(--text2)' }
              }>
              <Icon size={18} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-3 border-t" style={{ borderColor: 'var(--border)' }}>
          {!collapsed && (
            <div className="flex items-center gap-2 mb-2 px-1">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold text-white"
                   style={{ background: 'var(--accent)' }}>
                {user.nom_complet?.[0]?.toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold truncate">{user.nom_complet}</div>
                <div className="text-xs truncate" style={{ color: 'var(--text2)' }}>{ROLE_LABELS[user.role]}</div>
              </div>
            </div>
          )}
          <div className="flex gap-1">
            <button onClick={handleLogout}
                    className="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-gray-100"
                    style={{ color: 'var(--text2)' }}>
              <LogOut size={14} />
              {!collapsed && <span>Deconnexion</span>}
            </button>
            <button onClick={() => setCollapsed(!collapsed)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 transition-all"
                    style={{ color: 'var(--text2)' }}>
              {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>
          </div>
        </div>
      </aside>

      <main className={`flex-1 transition-all duration-200 ${collapsed ? 'ml-16' : 'ml-56'}`}>
        <Routes>
          <Route path="/login" element={<Navigate to={defaultRoute} replace />} />
          <Route path="/" element={
            <ProtectedRoute roles={['gestionnaire']}><CRMPage /></ProtectedRoute>
          } />
          <Route path="/conformite" element={
            <ProtectedRoute roles={['conformite']}><CompliancePage /></ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute roles={['admin']}><AdminPage /></ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to={defaultRoute} replace />} />
        </Routes>
      </main>
    </div>
  )
}
