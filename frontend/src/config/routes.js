import {
  Activity, Bell, BookOpen, ClipboardList, HeartPulse, History, LayoutDashboard,
  Plus, Stethoscope, UserRound, Users,
} from 'lucide-react'

export const ROLE = Object.freeze({ FARMER: 'farmer', DOCTOR: 'doctor', ADMIN: 'admin' })

export const ROUTES = Object.freeze({
  landing: '/', login: '/login', register: '/register',
  farmerHome: '/dashboard', cattle: '/cattle', newCheck: '/new-case',
  farmerCases: '/my-cases', vetDirectory: '/vets', notifications: '/notifications',
  result: '/diagnosis/:caseId', doctorHome: '/veterinary', queue: '/veterinary/queue',
  highRisk: '/veterinary/high-risk', doctorCases: '/veterinary/my-cases',
  reviewed: '/veterinary/reviewed', analytics: '/veterinary/analytics',
  knowledge: '/veterinary/knowledge', profile: '/veterinary/profile',
  caseReview: '/veterinary/cases/:caseId', adminHome: '/admin',
})

export function normalizeRole(role) {
  const normalized = String(role ?? '').trim().toLowerCase()
  return Object.values(ROLE).includes(normalized) ? normalized : null
}

export function homeForRole(role) {
  switch (normalizeRole(role)) {
    case ROLE.DOCTOR: return ROUTES.doctorHome
    case ROLE.ADMIN: return ROUTES.adminHome
    case ROLE.FARMER: return ROUTES.farmerHome
    default: return ROUTES.landing
  }
}

export const NAV_BY_ROLE = Object.freeze({
  [ROLE.FARMER]: [
    { to: ROUTES.farmerHome, label: 'Dashboard', mr: 'आढावा', icon: LayoutDashboard },
    { to: ROUTES.cattle, label: 'My cattle', mr: 'माझी जनावरे', icon: Stethoscope },
    { to: ROUTES.newCheck, label: 'New check', mr: 'नवीन तपासणी', icon: Plus },
    { to: ROUTES.farmerCases, label: 'My cases', mr: 'माझी प्रकरणे', icon: ClipboardList },
    { to: ROUTES.vetDirectory, label: 'Vet directory', mr: 'पशुवैद्यक सूची', icon: Users },
    { to: ROUTES.notifications, label: 'Notifications', mr: 'सूचना', icon: Bell },
  ],
  [ROLE.DOCTOR]: [
    { to: ROUTES.doctorHome, label: 'Dashboard', mr: 'आढावा', icon: LayoutDashboard },
    { to: ROUTES.queue, label: 'Case queue', mr: 'प्रकरण रांग', icon: ClipboardList },
    { to: ROUTES.highRisk, label: 'High-risk alerts', mr: 'उच्च जोखीम सूचना', icon: HeartPulse, badge: 'high' },
    { to: ROUTES.doctorCases, label: 'My cases', mr: 'माझी प्रकरणे', icon: Stethoscope },
    { to: ROUTES.reviewed, label: 'Reviewed history', mr: 'तपासलेला इतिहास', icon: History },
    { to: ROUTES.analytics, label: 'Analytics', mr: 'विश्लेषण', icon: Activity },
    { to: ROUTES.knowledge, label: 'Knowledge base', mr: 'ज्ञानसंग्रह', icon: BookOpen },
    { to: ROUTES.profile, label: 'Profile', mr: 'प्रोफाइल', icon: UserRound },
  ],
  [ROLE.ADMIN]: [
    { to: ROUTES.adminHome, label: 'Administration', mr: 'प्रशासन', icon: Users },
  ],
})

export function safeReturnTo(value) {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')) return null
  try {
    const parsed = new URL(value, window.location.origin)
    return parsed.origin === window.location.origin ? `${parsed.pathname}${parsed.search}${parsed.hash}` : null
  } catch { return null }
}
