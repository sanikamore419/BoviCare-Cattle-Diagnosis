import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)
const storageUser = () => { try { return JSON.parse(localStorage.getItem('bovicare_user') || 'null') } catch { return null } }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storageUser); const [loading, setLoading] = useState(Boolean(localStorage.getItem('bovicare_token')))
  const clearSession = () => { localStorage.removeItem('bovicare_token'); localStorage.removeItem('bovicare_user'); setUser(null) }
  const saveSession = ({ access_token, user: authenticatedUser }) => { localStorage.setItem('bovicare_token', access_token); localStorage.setItem('bovicare_user', JSON.stringify(authenticatedUser)); setUser(authenticatedUser) }
  useEffect(() => { const token = localStorage.getItem('bovicare_token'); if (!token) return; api.get('/auth/me').then(response => { localStorage.setItem('bovicare_user', JSON.stringify(response.data)); setUser(response.data) }).catch(clearSession).finally(() => setLoading(false)) }, [])
  useEffect(() => { const onExpired = () => clearSession(); window.addEventListener('bovicare:auth-expired', onExpired); return () => window.removeEventListener('bovicare:auth-expired', onExpired) }, [])
  async function login(credentials) { const response = await api.post('/auth/login', credentials); saveSession(response.data); return response.data.user }
  async function register(payload) { await api.post('/auth/register', payload); return login({ email: payload.email, password: payload.password }) }
  return <AuthContext.Provider value={{ user, loading, login, register, logout: clearSession }}>{children}</AuthContext.Provider>
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error('useAuth must be used inside AuthProvider'); return context }
