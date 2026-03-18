import React, { useState } from 'react'
import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { Building2, ShieldAlert, Menu, X, LogOut, User } from 'lucide-react'
import { useAuth } from './context/AuthContext'

import LoginPage      from './pages/LoginPage'
import CRMPage        from './pages/CRMPage'
import CompliancePage from './pages/CompliancePage'

const ROLE_LABELS = { admin: 'Administrateur', gestionnaire: 'Gestionnaire CRM', conformite: 'Agent Conformite' }

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
    hasRole('gestionnaire') && { to: '/',           icon: Building2,  label: 'CRM Fournisseurs' },
    hasRole('conformite')   && { to: '/conformite', icon: ShieldAlert, label: 'Conformite'      },
  ].filter(Boolean)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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

        {/* User info + logout */}
        <div className="px-3 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
          {!collapsed && (
            <div className="flex items-center gap-2 mb-3 px-1">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                   style={{ background: 'var(--accent)', opacity: 0.8 }}>
                <User size={14} className="text-white" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold truncate" style={{ color: 'var(--text)' }}>{user.nom_complet}</div>
                <div className="text-xs truncate" style={{ color: 'var(--text2)' }}>{ROLE_LABELS[user.role] || user.role}</div>
              </div>
            </div>
          )}
          <button onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium transition-all hover:bg-white/5"
                  style={{ color: 'var(--text2)' }}>
            <LogOut size={15} />
            {!collapsed && <span>Deconnexion</span>}
          </button>
        </div>
      </aside>

      <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-16' : 'ml-64'}`}>
        <Routes>
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="/" element={
            <ProtectedRoute roles={['gestionnaire']}>
              <CRMPage />
            </ProtectedRoute>
          } />
          <Route path="/conformite" element={
            <ProtectedRoute roles={['conformite']}>
              <CompliancePage />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
