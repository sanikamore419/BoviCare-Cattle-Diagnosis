import { ClipboardPlus, LayoutDashboard, LogOut, Menu, ShieldCheck, Stethoscope, UserRound, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../auth/LanguageContext'
import LanguageToggle from './LanguageToggle'

const links = [{ to: '/dashboard', label: 'Farmer dashboard', icon: LayoutDashboard }, { to: '/cattle', label: 'My cattle', icon: Stethoscope }, { to: '/new-case', label: 'New diagnosis', icon: ClipboardPlus }, { to: '/veterinary', label: 'Veterinary portal', icon: UserRound }]
function NavBrand() { return <NavLink to="/" className="mb-8 flex items-center gap-2 text-lg font-bold text-white"><span className="rounded-xl bg-emerald-400 p-2 text-emerald-950"><Stethoscope size={19} /></span>BoviCare AI</NavLink> }

export default function AppShell({ children }) {
  const [open, setOpen] = useState(false); const location = useLocation(); const { user, logout } = useAuth()
  const { language, translate } = useLanguage()
  const farmerLinks = [
    { to: '/dashboard', label: translate('Home', 'मुख्य पान'), icon: LayoutDashboard },
    { to: '/cattle', label: translate('My cattle', 'माझी जनावरे'), icon: Stethoscope },
    { to: '/new-case', label: translate('New check', 'नवीन तपासणी'), icon: ClipboardPlus },
  ]
  const visibleLinks = user?.role === 'farmer' ? farmerLinks : links
  const nav = <nav className="space-y-1.5">{visibleLinks.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${isActive ? 'bg-white text-emerald-900 shadow-sm' : 'text-emerald-50 hover:bg-emerald-800'}`}><Icon size={18} />{label}</NavLink>)}</nav>
  const title = user?.role === 'farmer' ? translate('Farmer services', 'शेतकरी सेवा') : location.pathname.startsWith('/veterinary') ? 'Veterinary workspace' : 'Farmer workspace'
  const account = <div className="mt-auto rounded-2xl border border-emerald-800 bg-emerald-900/60 p-4 text-sm text-emerald-50"><ShieldCheck className="mb-2 text-emerald-300" size={20} /><p className="font-semibold">{user?.name}</p><p className="mt-1 text-xs capitalize text-emerald-200">{user?.role === 'farmer' ? translate('Farmer account', 'शेतकरी खाते') : 'doctor account'}</p><button onClick={logout} className="mt-3 inline-flex items-center gap-2 text-xs font-bold text-emerald-100 hover:text-white"><LogOut size={15} />{user?.role === 'farmer' ? translate('Log out', 'बाहेर पडा') : 'Log out'}</button></div>
  return <div className="min-h-screen bg-[#f7faf7]"><aside className="fixed inset-y-0 left-0 z-40 hidden w-72 flex-col bg-emerald-950 p-5 lg:flex"><NavBrand />{nav}{user?.role === 'farmer' && <div className="mt-auto mb-4"><LanguageToggle /></div>}{account}</aside><header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur lg:ml-72"><div className="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6"><button onClick={() => setOpen(true)} aria-label="Open menu" className="rounded-lg p-2 text-slate-600 lg:hidden"><Menu /></button><p className="hidden text-sm font-semibold text-slate-600 lg:block">{title}</p><div className="ml-auto flex items-center gap-3">{user?.role === 'farmer' && <LanguageToggle />}<NavLink to="/" className="hidden text-sm font-bold text-emerald-800 sm:block">BoviCare AI</NavLink></div></div></header>{open && <div className="fixed inset-0 z-50 bg-slate-950/40 lg:hidden"><aside className="flex h-full w-72 flex-col bg-emerald-950 p-5 shadow-2xl"><div className="flex items-center justify-between"><NavBrand /><button onClick={() => setOpen(false)} aria-label="Close menu" className="p-2 text-white"><X /></button></div>{nav}{user?.role === 'farmer' && <div className="mt-5"><LanguageToggle /></div>}{account}</aside></div>}<main className="lg:ml-72"><div className="page-shell py-7 sm:py-10">{children}</div></main></div>
}
