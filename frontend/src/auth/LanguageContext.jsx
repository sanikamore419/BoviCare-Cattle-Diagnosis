import { createContext, useCallback, useContext, useState } from 'react'

const LanguageContext = createContext(null)

function storedLanguage() {
  try {
    return localStorage.getItem('bovicare_language') === 'mr' ? 'mr' : 'en'
  } catch {
    return 'en'
  }
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(storedLanguage)
  function setLanguage(nextLanguage) {
    const next = nextLanguage === 'mr' ? 'mr' : 'en'
    setLanguageState(next)
    try { localStorage.setItem('bovicare_language', next) } catch { /* Preference storage is optional. */ }
  }
  const translate = useCallback((english, marathi) => language === 'mr' ? marathi : english, [language])
  return <LanguageContext.Provider value={{ language, setLanguage, translate }}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const value = useContext(LanguageContext)
  if (!value) throw new Error('useLanguage must be used inside LanguageProvider')
  return value
}
