import { createContext, useCallback, useContext, useEffect, useState } from 'react'

export const LanguageContext = createContext(null)
const SUPPORTED_LANGUAGES = Object.freeze(['en', 'hi', 'mr'])

function storedLanguage() {
  try {
    const stored = localStorage.getItem('bovicare_language')
    return SUPPORTED_LANGUAGES.includes(stored) ? stored : 'en'
  } catch {
    return 'en'
  }
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(storedLanguage)
  useEffect(() => { document.documentElement.lang = language }, [language])
  function setLanguage(nextLanguage) {
    const next = SUPPORTED_LANGUAGES.includes(nextLanguage) ? nextLanguage : 'en'
    setLanguageState(next)
    try { localStorage.setItem('bovicare_language', next) } catch { /* Preference storage is optional. */ }
  }
  const translate = useCallback((english, hindiOrMarathi, marathi) => {
    if (language === 'hi') return marathi === undefined ? english : hindiOrMarathi
    if (language === 'mr') return marathi === undefined ? hindiOrMarathi : marathi
    return english
  }, [language])
  return <LanguageContext.Provider value={{ language, setLanguage, translate, supportedLanguages: SUPPORTED_LANGUAGES }}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const value = useContext(LanguageContext)
  if (!value) throw new Error('useLanguage must be used inside LanguageProvider')
  return value
}
