import { useLanguage } from '../auth/LanguageContext'

const LANGUAGES = [
  { code: 'en', label: 'English', aria: 'Choose English' },
  { code: 'hi', label: 'हिन्दी', aria: 'हिन्दी चुनें' },
  { code: 'mr', label: 'मराठी', aria: 'मराठी निवडा' },
]

export default function LanguageToggle({ compact = false }) {
  const { language, setLanguage } = useLanguage()
  return (
    <div role="group" aria-label="Language / भाषा / भाषा" className={`inline-flex rounded-xl border border-emerald-200 bg-white p-1 ${compact ? 'gap-0' : 'gap-0.5'}`}>
      {LANGUAGES.map(({ code, label, aria }) => <button
        key={code}
        type="button"
        aria-label={aria}
        aria-pressed={language === code}
        onClick={() => setLanguage(code)}
        className={`min-h-10 rounded-lg px-2 text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-emerald-700 ${language === code ? 'bg-emerald-800 text-white' : 'text-slate-700 hover:bg-emerald-50'}`}
      >{label}</button>)}
    </div>
  )
}
