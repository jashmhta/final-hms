import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Import translation files
import en from './locales/en.json'
import es from './locales/es.json'
import fr from './locales/fr.json'
import de from './locales/de.json'
import ar from './locales/ar.json'

// Resources
const resources = {
  en: {
    translation: en,
  },
  es: {
    translation: es,
  },
  fr: {
    translation: fr,
  },
  de: {
    translation: de,
  },
  ar: {
    translation: ar,
  },
}

// Initialize i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',

    interpolation: {
      escapeValue: false, // React already escapes by default
    },

    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },

    react: {
      useSuspense: false,
    },
  })

// RTL language support
const isRTL = (lang: string) => {
  const rtlLanguages = ['ar']
  return rtlLanguages.includes(lang)
}

// Apply RTL class to body
const currentLang = i18n.language || 'en'
if (isRTL(currentLang)) {
  document.documentElement.dir = 'rtl'
  document.documentElement.lang = currentLang
} else {
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = currentLang
}

export default i18n
export { isRTL }