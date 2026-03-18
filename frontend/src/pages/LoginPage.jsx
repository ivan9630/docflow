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
      if (data.user.role === 'conformite') {
        navigate('/conformite')
      } else {
        navigate('/')
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
      <div className="w-full max-w-md p-8 rounded-2xl" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
               style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))' }}>
            <span className="text-white font-bold text-2xl">DF</span>
          </div>
          <h1 className="font-display font-bold text-2xl" style={{ color: 'var(--text)' }}>DocuFlow</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text2)' }}>Plateforme de traitement documentaire</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text2)' }}>Identifiant</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all"
              style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }}
              placeholder="admin"
              required
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text2)' }}>Mot de passe</label>
            <div className="relative">
              <input
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all pr-10"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }}
                placeholder="••••••••"
                required
              />
              <button type="button" onClick={() => setShowPw(!showPw)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100">
                {showPw ? <EyeOff size={16} style={{ color: 'var(--text2)' }} /> : <Eye size={16} style={{ color: 'var(--text2)' }} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all hover:opacity-90 disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))' }}
          >
            <LogIn size={16} />
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs text-center" style={{ color: 'var(--text2)' }}>
            Comptes de demo
          </p>
          <div className="flex justify-center gap-3 mt-3">
            {[
              { u: 'admin', label: 'Admin' },
              { u: 'gestionnaire', label: 'CRM' },
              { u: 'conformite', label: 'Conformite' },
            ].map(({ u, label }) => (
              <button
                key={u}
                type="button"
                onClick={() => { setUsername(u); setPassword(u === 'admin' ? 'admin123' : u === 'gestionnaire' ? 'gest123' : 'conf123') }}
                className="px-3 py-1.5 rounded-md text-xs font-mono transition-all hover:opacity-80"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text2)' }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
