import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { homeForRole, normalizeRole, safeReturnTo } from '../config/routes'

function SessionSkeleton() {
  return <main aria-label="Loading secure workspace" className="min-h-screen bg-[#F7F5EF] p-6">
    <div className="mx-auto max-w-6xl animate-pulse space-y-6" aria-hidden="true">
      <div className="h-14 rounded-2xl bg-white" />
      <div className="grid gap-6 md:grid-cols-[16rem_1fr]"><div className="h-[36rem] rounded-2xl bg-white" /><div className="space-y-5"><div className="h-36 rounded-2xl bg-white" /><div className="h-80 rounded-2xl bg-white" /></div></div>
    </div>
  </main>
}

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <SessionSkeleton />
  const role = normalizeRole(user?.role)
  if (!role) return <Navigate to="/login" replace state={{ returnTo: safeReturnTo(`${location.pathname}${location.search}`) }} />
  if (allowedRoles && !allowedRoles.includes(role)) return <Navigate to={homeForRole(role)} replace />
  return children
}
