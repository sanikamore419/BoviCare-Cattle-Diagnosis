import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)
const storageUser = () => { try { return JSON.parse(localStorage.getItem('bovicare_user') || 'null') } catch { return null } }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storageUser)
  const [loading, setLoading] = useState(true)

  function clearSession({ clearDrafts = true } = {}) {
    localStorage.removeItem('bovicare_token')
    localStorage.removeItem('bovicare_user')
    localStorage.removeItem('bovicare_last_activity')
    if (clearDrafts) sessionStorage.removeItem('bovicare_new_case_draft')
    if ('caches' in window) window.caches.keys().then(keys => keys.forEach(key => window.caches.delete(key))).catch(() => { /* Cache storage is optional. */ })
    setUser(null)
  }

  function saveSession(session) {
    localStorage.setItem('bovicare_token', session.access_token)
    localStorage.setItem('bovicare_user', JSON.stringify(session.user))
    localStorage.setItem('bovicare_last_activity', String(Date.now()))
    setUser(session.user)
  }

  useEffect(() => {
    let active = true
    const token = localStorage.getItem('bovicare_token')
    const rehydrate = token ? api.get('/auth/me') : api.post('/auth/refresh')
    rehydrate
      .then(response => {
        if (!active) return
        if (response.data.access_token) saveSession(response.data)
        else {
          localStorage.setItem('bovicare_user', JSON.stringify(response.data))
          localStorage.setItem('bovicare_last_activity', String(Date.now()))
          setUser(response.data)
        }
      })
      .catch(() => { if (active) clearSession() })
      .finally(() => { if (active) setLoading(false) })

    const onExpired = () => clearSession({ clearDrafts: false })
    const onStorage = event => {
      if (event.key === 'bovicare_user') setUser(storageUser())
      if (event.key === 'bovicare_token' && event.newValue === null) setUser(null)
      if (event.key === 'bovicare_logout' && event.newValue) clearSession()
    }
    window.addEventListener('bovicare:auth-expired', onExpired)
    window.addEventListener('storage', onStorage)
    return () => {
      active = false
      window.removeEventListener('bovicare:auth-expired', onExpired)
      window.removeEventListener('storage', onStorage)
    }
  }, [])

  async function login(credentials) {
    const response = await api.post('/auth/login', credentials)
    saveSession(response.data)
    return response.data.user
  }

  async function register(payload) {
    await api.post('/auth/register', payload)
    return login({ email: payload.email, password: payload.password })
  }

  async function logout() {
    try { await api.post('/auth/logout') } finally {
      clearSession()
      localStorage.setItem('bovicare_logout', String(Date.now()))
      localStorage.removeItem('bovicare_logout')
    }
  }

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
