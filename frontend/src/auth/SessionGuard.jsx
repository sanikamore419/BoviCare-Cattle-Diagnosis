import { useEffect, useRef, useState } from 'react'
import { LogOut, ShieldCheck } from 'lucide-react'
import { useAuth } from './AuthContext'
import { useLanguage } from './LanguageContext'

const IDLE_LIMIT_MS = 30 * 60 * 1000
const WARNING_MS = 60 * 1000
const LAST_ACTIVITY_KEY = 'bovicare_last_activity'
const ACTIVITY_EVENTS = ['pointerdown', 'keydown', 'touchstart', 'scroll']

export default function SessionGuard() {
  const { user, logout } = useAuth()
  const { translate } = useLanguage()
  const [now, setNow] = useState(Date.now())
  const [lastActivity, setLastActivity] = useState(() => Number(localStorage.getItem(LAST_ACTIVITY_KEY)) || Date.now())
  const signingOut = useRef(false)

  useEffect(() => {
    if (!user) return undefined
    const updateActivity = () => {
      const timestamp = Date.now()
      localStorage.setItem(LAST_ACTIVITY_KEY, String(timestamp))
      setLastActivity(timestamp)
    }
    const onStorage = event => {
      if (event.key === LAST_ACTIVITY_KEY && Number(event.newValue) > lastActivity) setLastActivity(Number(event.newValue))
    }
    ACTIVITY_EVENTS.forEach(type => window.addEventListener(type, updateActivity, { passive: true }))
    window.addEventListener('storage', onStorage)
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => {
      ACTIVITY_EVENTS.forEach(type => window.removeEventListener(type, updateActivity))
      window.removeEventListener('storage', onStorage)
      window.clearInterval(timer)
    }
  }, [user, lastActivity])

  const remaining = lastActivity + IDLE_LIMIT_MS + WARNING_MS - now
  const warning = Boolean(user) && remaining <= WARNING_MS && remaining > 0
  useEffect(() => {
    if (user && remaining <= 0 && !signingOut.current) {
      signingOut.current = true
      logout()
    }
  }, [user, remaining, logout])

  useEffect(() => { if (!user) signingOut.current = false }, [user])

  if (!warning) return null
  const seconds = Math.ceil(remaining / 1000)
  function staySignedIn() {
    const timestamp = Date.now()
    localStorage.setItem(LAST_ACTIVITY_KEY, String(timestamp))
    setLastActivity(timestamp)
    setNow(timestamp)
  }

  return <div className="fixed inset-0 z-[100] grid place-items-center bg-slate-950/50 p-4" role="presentation">
    <section role="alertdialog" aria-modal="true" aria-labelledby="idle-title" className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl">
      <ShieldCheck className="text-emerald-800" size={24} />
      <h2 id="idle-title" className="mt-4 text-xl font-bold text-slate-900">{translate('Are you still there?', 'क्या आप अभी भी यहाँ हैं?', 'तुम्ही अजून येथे आहात का?')}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{translate(`You will be signed out in ${seconds} seconds to protect your account.`, `आपके खाते की सुरक्षा के लिए ${seconds} सेकंड में आपको साइन आउट कर दिया जाएगा।`, `तुमचे खाते सुरक्षित ठेवण्यासाठी ${seconds} सेकंदांत तुम्हाला साइन आउट केले जाईल.`)}</p>
      <div className="mt-5 flex flex-wrap justify-end gap-3">
        <button className="button-secondary" onClick={logout}><LogOut size={16} />{translate('Log out', 'साइन आउट करें', 'बाहेर पडा')}</button>
        <button className="button-primary" onClick={staySignedIn}>{translate('Stay signed in', 'साइन इन रहें', 'साइन इन राहा')}</button>
      </div>
    </section>
  </div>
}
