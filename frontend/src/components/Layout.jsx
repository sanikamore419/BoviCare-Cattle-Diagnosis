import { Activity, ClipboardPlus, LayoutDashboard, Stethoscope, UserRound } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const links = [{ to: '/', label: 'Dashboard', icon: LayoutDashboard }, { to: '/new-case', label: 'New assessment', icon: ClipboardPlus }, { to: '/veterinary', label: 'Veterinary review', icon: UserRound }]

export default function Layout({ children }) {
  return <div className="min-h-screen md:flex"><aside className="bg-emerald-900 p-6 text-white md:w-64"><div className="mb-10 flex items-center gap-2 text-xl font-bold"><Stethoscope /> BoviCare AI</div><nav className="space-y-2">{links.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 ${isActive ? 'bg-emerald-700' : 'hover:bg-emerald-800'}`}><Icon size={19} />{label}</NavLink>)}</nav><p className="mt-12 text-xs leading-5 text-emerald-100"><Activity className="mb-2" size={18} />Clinical decision support only. Seek veterinary advice for treatment.</p></aside><main className="mx-auto w-full max-w-6xl p-6 md:p-10">{children}</main></div>
}
