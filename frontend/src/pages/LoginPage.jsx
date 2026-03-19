import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { loginUser } from '../api'
import toast from 'react-hot-toast'
import { LogIn, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await loginUser(username, password)
      login(data.access_token, data.user)
      toast.success(`Bienvenue, ${data.user.nom_complet}`)
      navigate(data.user.role === 'conformite' ? '/conformite' : data.user.role === 'admin' ? '/admin' : '/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f0f2f5 0%, #e8ecf4 100%)' }}>
      <div className="w-full max-w-[380px] mx-4">
        <div className="rounded-2xl p-8" style={{ background: 'var(--surface)', boxShadow: '0 4px 24px rgba(0,0,0,0.06)', border: '1px solid var(--border-light)' }}>
          <div className="text-center mb-7">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3"
                 style={{ background: 'var(--accent)', boxShadow: '0 4px 12px rgba(79,110,247,0.3)' }}>
              <span className="text-white font-bold text-lg">DF</span>
            </div>
            <h1 className="font-bold text-xl" style={{ color: 'var(--text)' }}>DocuFlow</h1>
            <p className="text-[13px] mt-1" style={{ color: 'var(--text2)' }}>Connectez-vous pour continuer</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[12px] font-medium mb-1.5" style={{ color: 'var(--text2)' }}>Identifiant</label>
              <input type="text" value={username} onChange={e => setUsername(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg text-sm outline-none transition-all focus:ring-2 focus:ring-blue-100"
                style={{ background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                required autoFocus />
            </div>
            <div>
              <label className="block text-[12px] font-medium mb-1.5" style={{ color: 'var(--text2)' }}>Mot de passe</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg text-sm outline-none transition-all pr-10 focus:ring-2 focus:ring-blue-100"
                  style={{ background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                  required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 opacity-40 hover:opacity-80 transition-opacity">
                  {showPw ? <EyeOff size={16} style={{ color: 'var(--text2)' }} /> : <Eye size={16} style={{ color: 'var(--text2)' }} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all hover:brightness-95 disabled:opacity-50"
              style={{ background: 'var(--accent)', boxShadow: '0 2px 8px rgba(79,110,247,0.3)' }}>
              <LogIn size={16} />
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>

          <div className="mt-6 pt-5" style={{ borderTop: '1px solid var(--border-light)' }}>
            <p className="text-[11px] text-center font-medium mb-3" style={{ color: 'var(--text3)' }}>COMPTES DEMO</p>
            <div className="flex justify-center gap-2">
              {[
                { u: 'admin', p: 'admin123', label: 'Admin', color: '#4f6ef7' },
                { u: 'gestionnaire', p: 'gest123', label: 'CRM', color: '#10b981' },
                { u: 'conformite', p: 'conf123', label: 'Conformite', color: '#8b5cf6' },
              ].map(({ u, p, label, color }) => (
                <button key={u} type="button"
                  onClick={() => { setUsername(u); setPassword(p) }}
                  className="px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all hover:brightness-95"
                  style={{ background: color + '0d', border: `1px solid ${color}25`, color }}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
