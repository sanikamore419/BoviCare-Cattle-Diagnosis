import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { homeForRole } from '../config/routes'
import { useLanguage } from '../auth/LanguageContext'

export default function NotFound() {
  const { user } = useAuth()
  const { translate } = useLanguage()
  return <main className="grid min-h-screen place-items-center bg-[#F7F5EF] p-5">
    <section className="surface w-full max-w-lg p-8 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-2xl font-bold">{translate('Page not found', 'पृष्ठ सापडले नाही')}</h1>
      <p className="mt-2 text-slate-600">{translate('This page may have moved or is not available.', 'हे पृष्ठ हलवले गेले असावे किंवा उपलब्ध नाही.')}</p>
      <Link className="button-primary mt-6" to={homeForRole(user?.role)}>{translate('Back to dashboard', 'आढाव्यावर परत जा')}</Link>
    </section>
  </main>
}
