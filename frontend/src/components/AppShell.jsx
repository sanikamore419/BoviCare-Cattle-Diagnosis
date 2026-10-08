import { Bell, ChevronDown, ChevronLeft, ChevronRight, LogOut, Menu, ShieldCheck, Stethoscope, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../auth/LanguageContext'
import { NAV_BY_ROLE, normalizeRole, ROLE } from '../config/routes'
import { api } from '../lib/api'
import LanguageToggle from './LanguageToggle'

const COLLAPSED_KEY = 'bovicare_sidebar_collapsed'
const EMPTY_NAV = []

function Brand({ compact = false }) {
  return <Link to="/" aria-label="BoviCare AI home" className={`flex shrink-0 items-center gap-2 text-lg font-bold text-white ${compact ? 'justify-center' : ''}`}>
    <span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-400 text-emerald-950"><Stethoscope size={20} strokeWidth={1.75} /></span>
    {!compact && <span>BoviCare AI</span>}
  </Link>
}

export default function AppShell({ children }) {
  const location = useLocation()
  const { user, logout } = useAuth()
  const { language } = useLanguage()
  const role = normalizeRole(user?.role)
  const navItems = NAV_BY_ROLE[role] || EMPTY_NAV
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSED_KEY) === 'true')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [highRiskCount, setHighRiskCount] = useState(null)

  useEffect(() => {
    localStorage.setItem(COLLAPSED_KEY, String(collapsed))
  }, [collapsed])

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
  const pageTitle = current?.label || (location.pathname.startsWith('/diagnosis/') ? 'Check result' : 'BoviCare workspace')
  const baseWidth = collapsed ? 'lg:ml-[5.5rem]' : 'lg:ml-72'
  const sidebarWidth = collapsed ? 'w-[5.5rem]' : 'w-72'

  function Navigation({ mobile = false }) {
    return <nav aria-label={role === ROLE.DOCTOR ? 'Doctor navigation' : 'Farmer navigation'} className="space-y-1.5">
      {navItems.map(({ to, label, mr, icon: Icon, badge }) => {
        const shownLabel = language === 'mr' ? mr : label
        const count = badge === 'high' ? highRiskCount : null
        return <NavLink key={to} to={to} title={collapsed && !mobile ? shownLabel : undefined} onClick={() => mobile && setDrawerOpen(false)} className={({ isActive }) => `group flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white ${isActive ? 'bg-white text-emerald-900 shadow-sm' : 'text-emerald-50 hover:bg-emerald-800'}`}>
          <Icon className="shrink-0" size={20} strokeWidth={1.75} />
          {(!collapsed || mobile) && <span className="min-w-0 flex-1 truncate">{shownLabel}</span>}
          {count !== null && count > 0 && <span aria-label={`${count} high-risk cases`} className="ml-auto inline-flex min-w-6 items-center justify-center rounded-full bg-amber-400 px-1.5 py-0.5 text-xs font-bold text-slate-950">{count}</span>}
        </NavLink>
      })}
    </nav>
  }

  const notificationTo = role === ROLE.DOCTOR ? '/veterinary/high-risk' : '/notifications'
  const roleLabel = role === ROLE.DOCTOR ? 'Veterinary doctor' : role === ROLE.ADMIN ? 'Administrator' : 'Farmer'

  return <div className="min-h-screen bg-[#F7F5EF]">
    <aside className={`fixed inset-y-0 left-0 z-30 hidden flex-col bg-[#14532D] p-4 transition-[width] duration-200 lg:flex ${sidebarWidth}`}>
      <div className={`mb-8 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}><Brand compact={collapsed} />
        {!collapsed && <button aria-label="Collapse sidebar" onClick={() => setCollapsed(true)} className="rounded-lg p-2 text-emerald-100 hover:bg-emerald-800"><ChevronLeft size={18} /></button>}
      </div>
      {collapsed && <button aria-label="Expand sidebar" onClick={() => setCollapsed(false)} className="mb-4 self-center rounded-lg p-2 text-emerald-100 hover:bg-emerald-800"><ChevronRight size={18} /></button>}
      <Navigation />
      <div className="mt-auto border-t border-emerald-800 pt-4">
        <div className={`mb-4 ${collapsed ? 'flex justify-center' : ''}`}><LanguageToggle compact={collapsed} /></div>
        {!collapsed && <p className="flex items-center gap-2 px-2 text-xs text-emerald-100"><ShieldCheck size={16} />Secure {roleLabel.toLowerCase()} workspace</p>}
      </div>
    </aside>

    <div className={`min-h-screen transition-[margin] duration-200 ${baseWidth}`}>
      <header className="sticky top-0 z-20 border-b border-[#E7E5E4] bg-white/95 backdrop-blur">
        <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6">
          <button aria-label="Open navigation" onClick={() => setDrawerOpen(true)} className="rounded-lg p-2 text-slate-700 hover:bg-stone-100 lg:hidden"><Menu size={22} /></button>
          <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-700 sm:text-base">{language === 'mr' ? current?.mr || pageTitle : pageTitle}</p><p className="hidden text-xs text-slate-500 sm:block">{user?.name}</p></div>
          <LanguageToggle compact />
          <Link aria-label="Notifications" to={notificationTo} className="relative rounded-xl p-2.5 text-slate-700 hover:bg-stone-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700"><Bell size={20} strokeWidth={1.75} /></Link>
          <div className="relative">
            <button aria-expanded={userMenuOpen} onClick={() => setUserMenuOpen(open => !open)} className="flex min-h-11 items-center gap-2 rounded-xl border border-[#E7E5E4] px-2.5 text-left hover:bg-stone-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700 sm:px-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-900">{user?.name?.trim()?.[0]?.toUpperCase() || 'U'}</span>
              <span className="hidden max-w-36 sm:block"><span className="block truncate text-sm font-semibold text-slate-900">{user?.name}</span><span className="block text-xs capitalize text-slate-500">{roleLabel}</span></span>
              <ChevronDown size={16} className="hidden text-slate-500 sm:block" />
            </button>
            {userMenuOpen && <div className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-[#E7E5E4] bg-white p-2 shadow-lg">
              <div className="border-b border-stone-100 px-3 py-2"><p className="truncate text-sm font-semibold">{user?.name}</p><span className="mt-1 inline-flex rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-900">{roleLabel}</span></div>
              <button onClick={logout} className="flex min-h-11 w-full items-center gap-2 rounded-lg px-3 text-left text-sm font-semibold text-slate-700 hover:bg-stone-50"><LogOut size={16} />Log out</button>
            </div>}
          </div>
        </div>
      </header>
      <main className="page-shell py-7 sm:py-10">{children}</main>
    </div>

    {drawerOpen && <div className="fixed inset-0 z-50 bg-slate-950/45 lg:hidden" onClick={() => setDrawerOpen(false)}>
      <aside className="flex h-full w-[min(21rem,88vw)] flex-col bg-[#14532D] p-5 shadow-2xl" onClick={event => event.stopPropagation()}>
        <div className="mb-8 flex items-center justify-between"><Brand /><button aria-label="Close navigation" onClick={() => setDrawerOpen(false)} className="rounded-lg p-2 text-white hover:bg-emerald-800"><X size={21} /></button></div>
        <Navigation mobile />
        <div className="mt-auto border-t border-emerald-800 pt-4"><LanguageToggle /><p className="mt-4 text-xs text-emerald-100">{roleLabel} workspace</p></div>
      </aside>
    </div>}
  </div>
}
