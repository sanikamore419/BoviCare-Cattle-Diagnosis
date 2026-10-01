import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth(); const location = useLocation()
  if (loading) return <div className="flex min-h-screen items-center justify-center text-sm font-semibold text-emerald-800">Checking secure session…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to={user.role === 'doctor' ? '/veterinary' : '/dashboard'} replace />
  return children
}
