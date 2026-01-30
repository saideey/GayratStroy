import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { translations, LanguageCode, LANGUAGES } from '@/lib/translations'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/services/api'

type TranslationKeys = keyof typeof translations['uz']

interface LanguageContextType {
  language: LanguageCode
  setLanguage: (lang: LanguageCode) => Promise<void>
  t: (key: TranslationKeys) => string
  languages: typeof LANGUAGES
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user, isAuthenticated } = useAuthStore()
  const [language, setLanguageState] = useState<LanguageCode>(() => {
    // Try to get from localStorage first
    const saved = localStorage.getItem('language') as LanguageCode
    if (saved && ['uz', 'ru', 'uz_cyrl'].includes(saved)) {
      return saved
    }
    return 'uz'
  })

  // Sync with user's language preference when logged in
  useEffect(() => {
    if (isAuthenticated && user?.language) {
      setLanguageState(user.language as LanguageCode)
      localStorage.setItem('language', user.language)
    }
  }, [isAuthenticated, user?.language])

  const setLanguage = async (lang: LanguageCode) => {
    setLanguageState(lang)
    localStorage.setItem('language', lang)
    
    // If user is authenticated, save to server
    if (isAuthenticated) {
      try {
        await api.put('/users/language', { language: lang })
      } catch (error) {
        console.error('Failed to save language preference:', error)
      }
    }
  }

  const t = (key: TranslationKeys): string => {
    return translations[language][key] || translations['uz'][key] || key
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, languages: LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

export default LanguageContext
