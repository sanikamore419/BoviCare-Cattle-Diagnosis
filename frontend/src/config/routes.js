import {
  Activity, Bell, BookOpen, ClipboardList, HeartPulse, History, LayoutDashboard,
  Plus, Stethoscope, UserRound, Users,
} from 'lucide-react'

export const ROLE = Object.freeze({ FARMER: 'farmer', DOCTOR: 'doctor', ADMIN: 'admin' })
export const ROLE_VALUES = Object.freeze(Object.values(ROLE))

export const ROUTES = Object.freeze({
  landing: '/', login: '/login', register: '/register',
  farmerHome: '/dashboard', cattle: '/cattle', newCheck: '/new-case',
  farmerCases: '/my-cases', vetDirectory: '/vets', notifications: '/notifications',
  result: '/diagnosis/:caseId',
  doctorHome: '/veterinary', queue: '/veterinary/queue',
  highRisk: '/veterinary/high-risk', doctorCases: '/veterinary/my-cases',
  reviewed: '/veterinary/reviewed', analytics: '/veterinary/analytics',
  knowledge: '/veterinary/knowledge', profile: '/veterinary/profile',
  caseReview: '/veterinary/cases/:caseId', verificationPending: '/veterinary/verification-pending',
  adminHome: '/admin/overview', adminApprovals: '/admin/doctors',
})

export function normalizeRole(role) {
  const normalized = String(role ?? '').trim().toLowerCase()
  return ROLE_VALUES.includes(normalized) ? normalized : null
}

export function homeForRole(role) {
  switch (normalizeRole(role)) {
    case ROLE.DOCTOR: return ROUTES.doctorHome
    case ROLE.ADMIN: return ROUTES.adminHome
    case ROLE.FARMER: return ROUTES.farmerHome
    default: return ROUTES.landing
  }
}

const label = (en, hi, mr) => ({ en, hi, mr })

export const NAV_BY_ROLE = Object.freeze({
  [ROLE.FARMER]: [
    { to: ROUTES.farmerHome, label: label('Dashboard', 'डैशबोर्ड', 'आढावा'), icon: LayoutDashboard },
    { to: ROUTES.cattle, label: label('My cattle', 'मेरे पशु', 'माझी जनावरे'), icon: Stethoscope },
    { to: ROUTES.newCheck, label: label('New check', 'नई जाँच', 'नवीन तपासणी'), icon: Plus },
    { to: ROUTES.farmerCases, label: label('My cases', 'मेरे मामले', 'माझी प्रकरणे'), icon: ClipboardList },
    { to: ROUTES.vetDirectory, label: label('Vet directory', 'पशु चिकित्सक सूची', 'पशुवैद्यक सूची'), icon: Users },
    { to: ROUTES.notifications, label: label('Notifications', 'सूचनाएँ', 'सूचना'), icon: Bell },
  ],
  [ROLE.DOCTOR]: [
    { to: ROUTES.doctorHome, label: label('Dashboard', 'डैशबोर्ड', 'आढावा'), icon: LayoutDashboard },
    { to: ROUTES.queue, label: label('Case queue', 'मामलों की कतार', 'प्रकरणांची रांग'), icon: ClipboardList },
    { to: ROUTES.highRisk, label: label('High-risk alerts', 'उच्च जोखिम चेतावनी', 'उच्च जोखीम सूचना'), icon: HeartPulse, badge: 'high' },
    { to: ROUTES.doctorCases, label: label('My cases', 'मेरे मामले', 'माझी प्रकरणे'), icon: Stethoscope },
    { to: ROUTES.reviewed, label: label('Reviewed history', 'समीक्षित इतिहास', 'तपासलेला इतिहास'), icon: History },
    { to: ROUTES.analytics, label: label('Analytics', 'विश्लेषण', 'विश्लेषण'), icon: Activity },
    { to: ROUTES.knowledge, label: label('Knowledge base', 'ज्ञान आधार', 'ज्ञानसंग्रह'), icon: BookOpen },
    { to: ROUTES.profile, label: label('Profile', 'प्रोफ़ाइल', 'प्रोफाइल'), icon: UserRound },
  ],
  [ROLE.ADMIN]: [
    { to: ROUTES.adminApprovals, label: label('Doctor approvals', 'चिकित्सक अनुमोदन', 'डॉक्टर मंजुरी'), icon: Users },
    { to: ROUTES.adminHome, label: label('Overview', 'अवलोकन', 'आढावा'), icon: LayoutDashboard },
  ],
})

export function localizedLabel(value, language = 'en') {
  if (value && typeof value === 'object') return value[language] || value.en || ''
  return value || ''
}

export function safeReturnTo(value) {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || value.includes('\\') || [...value].some(character => character.charCodeAt(0) < 32)) return null
  try {
    const parsed = new URL(value, window.location.origin)
    return parsed.origin === window.location.origin ? `${parsed.pathname}${parsed.search}${parsed.hash}` : null
  } catch { return null }
}
