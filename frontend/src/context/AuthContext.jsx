import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem('docuflow_auth')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setToken(parsed.token)
        setUser(parsed.user)
      } catch { /* ignore */ }
    }
    setLoading(false)
  }, [])

  const login = (tokenValue, userData) => {
    setToken(tokenValue)
    setUser(userData)
    localStorage.setItem('docuflow_auth', JSON.stringify({ token: tokenValue, user: userData }))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('docuflow_auth')
  }

  const hasRole = (...roles) => {
    if (!user) return false
    return roles.includes(user.role) || user.role === 'admin'
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
