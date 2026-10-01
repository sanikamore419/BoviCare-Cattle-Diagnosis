import { useLanguage } from '../auth/LanguageContext'

export default function LanguageToggle() {
  const { language, setLanguage } = useLanguage()
  return (
    <div role="group" aria-label="Language" className="inline-flex rounded-md border border-emerald-200 bg-white p-1">
      <button type="button" aria-pressed={language === 'en'} onClick={() => setLanguage('en')} className={`min-h-10 rounded px-3 text-sm font-semibold ${language === 'en' ? 'bg-emerald-800 text-white' : 'text-slate-700 hover:bg-emerald-50'}`}>
        English
      </button>
      <button type="button" aria-pressed={language === 'mr'} onClick={() => setLanguage('mr')} className={`min-h-10 rounded px-3 text-sm font-semibold ${language === 'mr' ? 'bg-emerald-800 text-white' : 'text-slate-700 hover:bg-emerald-50'}`}>
        मराठी
      </button>
    </div>
  )
}