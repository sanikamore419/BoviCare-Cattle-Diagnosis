import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../auth/LanguageContext'
import { homeForRole } from '../config/routes'

export default function NotFound() {
  const { user } = useAuth()
  const { translate } = useLanguage()
  return <main className="grid min-h-screen place-items-center bg-[#F7F5EF] p-5">
    <section className="surface w-full max-w-lg p-8 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-2xl font-bold">{translate('Page not found', 'पृष्ठ नहीं मिला', 'पृष्ठ सापडले नाही')}</h1>
      <p className="mt-2 text-slate-600">{translate('This page may have moved or is not available.', 'यह पृष्ठ शायद स्थानांतरित हो गया है या उपलब्ध नहीं है।', 'हे पृष्ठ कदाचित हलवले गेले आहे किंवा उपलब्ध नाही.')}</p>
      <Link className="button-primary mt-6" to={homeForRole(user?.role)}>{translate('Back to dashboard', 'डैशबोर्ड पर लौटें', 'आढाव्यावर परत जा')}</Link>
    </section>
  </main>
}
