import { useEffect, useState } from 'react'
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import SessionGuard from './auth/SessionGuard'
import AppShell from './components/AppShell'
import ErrorBoundary from './components/ErrorBoundary'
import { LoginPage, RegisterPage } from './pages/AuthPage'
import CattleManagement from './pages/CattleManagement'
import Dashboard from './pages/Dashboard'
import DiagnosisResult from './pages/DiagnosisResult'
import Landing from './pages/Landing'
import NewCase from './pages/NewCase'
import NotFound from './pages/NotFound'
import VeterinaryCaseDetails from './pages/VeterinaryCaseDetails'
import VeterinaryDashboard from './pages/VeterinaryDashboard'
import WorkspacePlaceholder from './pages/WorkspacePlaceholder'
import { homeForRole, ROLE, ROUTES } from './config/routes'

function SessionExpiredRedirect() {
  const navigate = useNavigate()
  const location = useLocation()
  const [showToast, setShowToast] = useState(false)

  useEffect(() => {
    const onExpired = () => {
      const returnTo = `${location.pathname}${location.search}${location.hash}`
      setShowToast(true)
      navigate(ROUTES.login, { replace: true, state: { sessionExpired: true, returnTo } })
      window.setTimeout(() => setShowToast(false), 5000)
    }
    window.addEventListener('bovicare:auth-expired', onExpired)
    return () => window.removeEventListener('bovicare:auth-expired', onExpired)
  }, [location.pathname, location.search, location.hash, navigate])

  return showToast ? <div role="status" className="fixed right-4 top-4 z-[110] flex items-center gap-3 rounded-xl border border-amber-300 bg-white px-4 py-3 text-sm font-semibold text-slate-900 shadow-xl"><span className="h-2.5 w-2.5 rounded-full bg-amber-600" />Session expired. Sign in again to continue.</div> : null
}

function ProtectedPage({ roles, children }) {
  return <ProtectedRoute allowedRoles={roles}><AppShell>{children}</AppShell></ProtectedRoute>
}

function Placeholder({ title, description, actionTo = ROUTES.farmerHome, actionLabel = 'Open dashboard' }) {
  return <WorkspacePlaceholder title={title} description={description} actionTo={actionTo} actionLabel={actionLabel} />
}

export default function App() {
  const { user } = useAuth()
  const home = homeForRole(user?.role)

  return <>
    <SessionGuard />
    <SessionExpiredRedirect />
    <ErrorBoundary home={home}>
      <Routes>
        <Route path={ROUTES.landing} element={<Landing />} />
        <Route path={ROUTES.login} element={<LoginPage />} />
        <Route path={ROUTES.register} element={<RegisterPage />} />
        <Route path={ROUTES.farmerHome} element={<ProtectedPage roles={[ROLE.FARMER]}><Dashboard /></ProtectedPage>} />
        <Route path={ROUTES.cattle} element={<ProtectedPage roles={[ROLE.FARMER]}><CattleManagement /></ProtectedPage>} />
        <Route path={ROUTES.newCheck} element={<ProtectedPage roles={[ROLE.FARMER]}><NewCase /></ProtectedPage>} />
        <Route path={ROUTES.result} element={<ProtectedPage roles={[ROLE.FARMER]}><DiagnosisResult /></ProtectedPage>} />
        <Route path={ROUTES.farmerCases} element={<ProtectedPage roles={[ROLE.FARMER]}><Placeholder title="My cases" description="Your diagnosis history and veterinary advice" /></ProtectedPage>} />
        <Route path={ROUTES.vetDirectory} element={<ProtectedPage roles={[ROLE.FARMER]}><Placeholder title="Vet directory" description="Find veterinary support" /></ProtectedPage>} />
        <Route path={ROUTES.notifications} element={<ProtectedPage roles={[ROLE.FARMER]}><Placeholder title="Notifications" description="Updates about your cases" /></ProtectedPage>} />
        <Route path={ROUTES.doctorHome} element={<ProtectedPage roles={[ROLE.DOCTOR]}><VeterinaryDashboard /></ProtectedPage>} />
        <Route path={ROUTES.queue} element={<ProtectedPage roles={[ROLE.DOCTOR]}><VeterinaryDashboard /></ProtectedPage>} />
        <Route path={ROUTES.caseReview} element={<ProtectedPage roles={[ROLE.DOCTOR]}><VeterinaryCaseDetails /></ProtectedPage>} />
        <Route path={ROUTES.highRisk} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="High-risk alerts" description="Cases needing prompt veterinary review" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.doctorCases} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="My cases" description="Cases assigned to your account" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.reviewed} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="Reviewed history" description="Previously reviewed cases" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.analytics} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="Analytics" description="Clinical workload and case trends" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.knowledge} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="Knowledge base" description="Veterinary disease reference" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.profile} element={<ProtectedPage roles={[ROLE.DOCTOR]}><Placeholder title="Profile" description="Your veterinary account" actionTo={ROUTES.doctorHome} actionLabel="Open doctor dashboard" /></ProtectedPage>} />
        <Route path={ROUTES.adminHome} element={<ProtectedPage roles={[ROLE.ADMIN]}><Placeholder title="Administration" description="Administrative workspace" actionTo={ROUTES.adminHome} actionLabel="Administration" /></ProtectedPage>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  </>
}
