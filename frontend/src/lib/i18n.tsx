"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { en, type TranslationKey } from "./locales/en";
import { az } from "./locales/az";
import { ru } from "./locales/ru";

export type Language = "en" | "az" | "ru";
export type { TranslationKey };

const STORAGE_KEY = "ausa-language";

export const languageLabels: Record<Language, string> = {
  en: "EN",
  az: "AZ",
  ru: "RU",
};

export const translations = { en, az, ru };

type LanguageContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey | string, fallback?: string) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  // Restore the saved language on mount. This cannot become a lazy initial state: the
  // server render has no localStorage and would emit "en", so reading the saved value
  // during the first client render would produce a hydration mismatch.
  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (saved === "az" || saved === "ru") {
      setLanguage(saved);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  const translate = (key: TranslationKey | string, fallback?: string): string => {
    const activeDict = translations[language] as Record<string, string>;
    if (activeDict && activeDict[key]) {
      return activeDict[key];
    }
    const fallbackDict = translations.en as Record<string, string>;
    if (fallbackDict && fallbackDict[key]) {
      return fallbackDict[key];
    }
    return fallback ?? key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t: translate }}>
      {children}
    </LanguageContext.Provider>
  );
}

const defaultContextValue: LanguageContextValue = {
  language: "en",
  setLanguage: () => {},
  t: (key: TranslationKey | string, fallback?: string) =>
    translations.en[key as TranslationKey] || fallback || key,
};

export function useLanguage() {
  const context = useContext(LanguageContext);
  return context ?? defaultContextValue;
}
