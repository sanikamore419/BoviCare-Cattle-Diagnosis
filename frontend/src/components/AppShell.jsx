import { Bell, ChevronDown, ChevronLeft, ChevronRight, LogOut, Menu, ShieldCheck, Stethoscope, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../auth/LanguageContext'
import { homeForRole, localizedLabel, NAV_BY_ROLE, normalizeRole, ROLE, ROUTES } from '../config/routes'
import { api } from '../lib/api'
import LanguageToggle from './LanguageToggle'

const COLLAPSED_KEY = 'bovicare_sidebar_collapsed'
const EMPTY_NAV = []
const ROLE_LABEL = {
  farmer: { en: 'Farmer', hi: 'किसान', mr: 'शेतकरी' },
  doctor: { en: 'Veterinary doctor', hi: 'पशु चिकित्सक', mr: 'पशुवैद्यक' },
  admin: { en: 'Administrator', hi: 'प्रशासक', mr: 'प्रशासक' },
}

function Brand({ compact = false, to }) {
  return <Link to={to} aria-label="BoviCare AI" className={`flex shrink-0 items-center gap-2 text-lg font-bold text-white ${compact ? 'justify-center' : ''}`}>
    <span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-400 text-emerald-950"><Stethoscope size={20} strokeWidth={1.75} /></span>
    {!compact && <span>BoviCare AI</span>}
  </Link>
}

export default function AppShell({ children }) {
  const location = useLocation()
  const { user, logout } = useAuth()
  const { language, translate } = useLanguage()
  const role = normalizeRole(user?.role)
  const navItems = NAV_BY_ROLE[role] || EMPTY_NAV
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSED_KEY) === 'true')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [highRiskCount, setHighRiskCount] = useState(null)
  const roleLabel = localizedLabel(ROLE_LABEL[role], language)
  const tr = translate

  useEffect(() => { localStorage.setItem(COLLAPSED_KEY, String(collapsed)) }, [collapsed])

  // This uses the existing /cases endpoint; the contract file is absent from this checkout.
  useEffect(() => {
    if (role !== ROLE.DOCTOR) return undefined
    let active = true
    api.get('/cases').then(response => {
      if (active) setHighRiskCount((response.data || []).filter(item => (item.urgency_level || item.risk_level || '').toUpperCase() === 'HIGH').length)
    }).catch(() => { if (active) setHighRiskCount(null) })
    return () => { active = false }
  }, [role])

  useEffect(() => { setDrawerOpen(false); setUserMenuOpen(false) }, [location.pathname])

  const current = useMemo(() => navItems.find(item => location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(`${item.to}/`))), [navItems, location.pathname])
  const routeTitle = current ? localizedLabel(current.label, language) : tr('BoviCare workspace', 'BoviCare कार्यक्षेत्र', 'BoviCare कार्यक्षेत्र')
  const pageTitle = location.pathname.startsWith('/diagnosis/') ? tr('Check result', 'जाँच का परिणाम', 'तपासणीचा निकाल') : routeTitle
  const baseWidth = collapsed ? 'lg:ml-[5.5rem]' : 'lg:ml-72'
  const sidebarWidth = collapsed ? 'w-[5.5rem]' : 'w-72'
  const home = homeForRole(role)
  const displayName = user?.full_name || user?.name || user?.email || ''
  const notificationTo = role === ROLE.DOCTOR ? ROUTES.highRisk : ROUTES.notifications

  function Navigation({ mobile = false }) {
    return <nav aria-label={tr(`${roleLabel} navigation`, `${roleLabel} नेविगेशन`, `${roleLabel} नेव्हिगेशन`)} className="space-y-1.5">
      {navItems.map(({ to, label, icon: Icon, badge }) => {
        const shownLabel = localizedLabel(label, language)
        const count = badge === 'high' ? highRiskCount : null
        const countLabel = tr(`${count} high-risk cases`, `${count} उच्च जोखिम वाले मामले`, `${count} उच्च जोखीम प्रकरणे`)
        return <NavLink key={to} to={to} title={collapsed && !mobile ? shownLabel : undefined} onClick={() => mobile && setDrawerOpen(false)} className={({ isActive }) => `group flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white ${isActive ? 'bg-white text-emerald-900 shadow-sm' : 'text-emerald-50 hover:bg-emerald-800'}`}>
          <Icon className="shrink-0" size={20} strokeWidth={1.75} />
          {(!collapsed || mobile) && <span className="min-w-0 flex-1 break-words">{shownLabel}</span>}
          {count !== null && count > 0 && <span aria-label={countLabel} className="ml-auto inline-flex min-w-6 items-center justify-center rounded-full bg-amber-400 px-1.5 py-0.5 text-xs font-bold text-slate-950">{count}</span>}
        </NavLink>
      })}
    </nav>
  }

  return <div className="min-h-screen bg-[#F7F5EF]">
    <aside className={`fixed inset-y-0 left-0 z-30 hidden flex-col bg-[#14532D] p-4 transition-[width] duration-200 lg:flex ${sidebarWidth}`}>
      <div className={`mb-8 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}><Brand compact={collapsed} to={home} />
        {!collapsed && <button aria-label={tr('Collapse sidebar', 'साइडबार छोटा करें', 'साइडबार लहान करा')} onClick={() => setCollapsed(true)} className="rounded-lg p-2 text-emerald-100 hover:bg-emerald-800"><ChevronLeft size={18} /></button>}
      </div>
      {collapsed && <button aria-label={tr('Expand sidebar', 'साइडबार खोलें', 'साइडबार उघडा')} onClick={() => setCollapsed(false)} className="mb-4 self-center rounded-lg p-2 text-emerald-100 hover:bg-emerald-800"><ChevronRight size={18} /></button>}
      <Navigation />
      <div className="mt-auto border-t border-emerald-800 pt-4">
        <div className={`mb-4 ${collapsed ? 'flex justify-center' : ''}`}><LanguageToggle compact={collapsed} /></div>
        {!collapsed && <p className="flex items-center gap-2 px-2 text-xs text-emerald-100"><ShieldCheck size={16} />{tr(`${roleLabel} workspace`, `${roleLabel} कार्यक्षेत्र`, `${roleLabel} कार्यक्षेत्र`)}</p>}
      </div>
    </aside>

    <div className={`min-h-screen transition-[margin] duration-200 ${baseWidth}`}>
      <header className="sticky top-0 z-20 border-b border-[#E7E5E4] bg-white/95 backdrop-blur">
        <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6">
          <button aria-label={tr('Open navigation', 'नेविगेशन खोलें', 'नेव्हिगेशन उघडा')} aria-expanded={drawerOpen} onClick={() => setDrawerOpen(true)} className="rounded-lg p-2 text-slate-700 hover:bg-stone-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700 lg:hidden"><Menu size={22} /></button>
          <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-700 sm:text-base">{pageTitle}</p><p className="hidden text-xs text-slate-500 sm:block">{displayName}</p></div>
          <LanguageToggle compact />
          <Link aria-label={tr('Notifications', 'सूचनाएँ', 'सूचना')} to={notificationTo} className="relative rounded-xl p-2.5 text-slate-700 hover:bg-stone-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700"><Bell size={20} strokeWidth={1.75} /></Link>
          <div className="relative">
            <button aria-expanded={userMenuOpen} aria-haspopup="menu" onClick={() => setUserMenuOpen(open => !open)} className="flex min-h-11 items-center gap-2 rounded-xl border border-[#E7E5E4] px-2.5 text-left hover:bg-stone-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700 sm:px-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-900">{displayName.trim()?.[0]?.toUpperCase() || 'U'}</span>
              <span className="hidden max-w-36 sm:block"><span className="block truncate text-sm font-semibold text-slate-900">{displayName}</span><span className="block text-xs text-slate-500">{roleLabel}</span></span>
              <ChevronDown size={16} className="hidden text-slate-500 sm:block" />
            </button>
            {userMenuOpen && <div role="menu" className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-[#E7E5E4] bg-white p-2 shadow-lg">
              <div className="border-b border-stone-100 px-3 py-2"><p className="truncate text-sm font-semibold">{displayName}</p><span className="mt-1 inline-flex max-w-full break-words rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-900">{roleLabel}</span></div>
              <button role="menuitem" onClick={logout} className="flex min-h-11 w-full items-center gap-2 rounded-lg px-3 text-left text-sm font-semibold text-slate-700 hover:bg-stone-50"><LogOut size={16} />{tr('Log out', 'लॉग आउट', 'लॉग आउट')}</button>
            </div>}
          </div>
        </div>
      </header>
      <main className="page-shell py-7 sm:py-10">{children}</main>
    </div>

    {drawerOpen && <div className="fixed inset-0 z-50 bg-slate-950/45 lg:hidden" onClick={() => setDrawerOpen(false)}>
      <aside aria-label={tr('Mobile navigation', 'मोबाइल नेविगेशन', 'मोबाइल नेव्हिगेशन')} className="flex h-full w-[min(21rem,88vw)] flex-col bg-[#14532D] p-5 shadow-2xl" onClick={event => event.stopPropagation()}>
        <div className="mb-8 flex items-center justify-between"><Brand to={home} /><button aria-label={tr('Close navigation', 'नेविगेशन बंद करें', 'नेव्हिगेशन बंद करा')} onClick={() => setDrawerOpen(false)} className="rounded-lg p-2 text-white hover:bg-emerald-800"><X size={21} /></button></div>
        <Navigation mobile />
        <div className="mt-auto border-t border-emerald-800 pt-4"><LanguageToggle /><p className="mt-4 text-xs text-emerald-100">{tr(`${roleLabel} workspace`, `${roleLabel} कार्यक्षेत्र`, `${roleLabel} कार्यक्षेत्र`)}</p></div>
      </aside>
    </div>}
  </div>
}
