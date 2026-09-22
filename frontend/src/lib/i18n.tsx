"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Language = "en" | "az" | "ru";
const STORAGE_KEY = "ausa-language";

export const languageLabels: Record<Language, string> = { en: "EN", az: "AZ", ru: "RU" };

type TranslationKey =
  | "home" | "plan" | "target" | "azerbaijan" | "advisor" | "application" | "applications"
  | "universityAdvisor" | "skipToContent" | "openNavigation" | "closeNavigation" | "language"
  | "finance" | "scholarships" | "dimCalculator" | "sopChecker" | "timeline"
  | "more"
  | "currentBuild" | "workingSurfaces" | "azerbaijanDescription" | "open" | "product"
  | "routePlanning" | "targetUniversity" | "aiAdvisor" | "applicationAssistant" | "information"
  | "howItWorks" | "aboutProject" | "heroPhotoCredit";

const translations: Record<Language, Record<TranslationKey, string>> = {
  en: {
    home: "Home", plan: "Plan my route", target: "Target University", azerbaijan: "Azerbaijan DİM", advisor: "AI advisor", application: "Application", applications: "My Tracker", finance: "Finances & Visa", scholarships: "Scholarships", dimCalculator: "DİM Calculator", sopChecker: "SOP & CV Checker", timeline: "Admissions Calendar", more: "More", universityAdvisor: "University advisor", skipToContent: "Skip to content", openNavigation: "Open navigation", closeNavigation: "Close navigation", language: "Language", currentBuild: "Current build", workingSurfaces: "Working surfaces, clearly labelled.", azerbaijanDescription: "Explore projected domestic DİM cutoffs from Azerbaijan admission history, including full-scholarship benchmarks and uncertainty bands.", open: "Open", product: "Product", routePlanning: "Route planning", targetUniversity: "Target University", aiAdvisor: "AI advisor", applicationAssistant: "Application assistant", information: "Information", howItWorks: "How it works", aboutProject: "About the project", heroPhotoCredit: "Hero photo credit"
  },
  az: {
    home: "Ana səhifə", plan: "Marşrutumu planla", target: "Hədəf universitet", azerbaijan: "Azərbaycan DİM", advisor: "Süni intellekt məsləhətçisi", application: "Müraciət", applications: "Müraciətlərim", finance: "Maliyyə və viza", scholarships: "Təqaüdlər", dimCalculator: "DİM kalkulyatoru", sopChecker: "SOP və CV yoxlayıcı", timeline: "Qəbul təqvimi", more: "Daha çox", universityAdvisor: "Universitet məsləhətçisi", skipToContent: "Məzmunu keç", openNavigation: "Naviqasiyanı aç", closeNavigation: "Naviqasiyanı bağla", language: "Dil", currentBuild: "Cari versiya", workingSurfaces: "İşlək bölmələr aydın göstərilir.", azerbaijanDescription: "Azərbaycan qəbul tarixçəsinə əsasən DİM keçid ballarının proqnozlarını, tam təqaüd meyarlarını və qeyri-müəyyənlik diapazonlarını araşdırın.", open: "Aç", product: "Platforma", routePlanning: "Marşrut planlaşdırılması", targetUniversity: "Hədəf universitet", aiAdvisor: "Süni intellekt məsləhətçisi", applicationAssistant: "Müraciət köməkçisi", information: "Məlumat", howItWorks: "Necə işləyir", aboutProject: "Layihə haqqında", heroPhotoCredit: "Şəkil mənbəyi"
  },
  ru: {
    home: "Главная", plan: "Спланировать маршрут", target: "Целевой университет", azerbaijan: "Азербайджанский DİM", advisor: "ИИ-консультант", application: "Заявка", applications: "Мои заявки", finance: "Финансы и виза", scholarships: "Стипендии", dimCalculator: "Калькулятор DİM", sopChecker: "Проверка SOP и CV", timeline: "Календарь поступления", more: "Ещё", universityAdvisor: "Консультант по университетам", skipToContent: "Перейти к содержимому", openNavigation: "Открыть навигацию", closeNavigation: "Закрыть навигацию", language: "Язык", currentBuild: "Текущая версия", workingSurfaces: "Рабочие разделы с понятным статусом.", azerbaijanDescription: "Изучайте прогнозы проходных баллов DİM на основе истории поступления в Азербайджане, включая пороги полной стипендии и диапазоны неопределённости.", open: "Открыть", product: "Продукт", routePlanning: "Планирование маршрута", targetUniversity: "Целевой университет", aiAdvisor: "ИИ-консультант", applicationAssistant: "Помощник по заявке", information: "Информация", howItWorks: "Как это работает", aboutProject: "О проекте", heroPhotoCredit: "Источник фотографии"
  }
};

type LanguageContextValue = { language: Language; setLanguage: (language: Language) => void; t: (key: TranslationKey) => string };
const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  // Restore the saved language on mount. This cannot become a lazy initial state: the
  // server render has no localStorage and would emit "en", so reading the saved value
  // during the first client render would produce a hydration mismatch.
  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (saved === "az" || saved === "ru") setLanguage(saved);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  return <LanguageContext.Provider value={{ language, setLanguage, t: (key) => translations[language][key] }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
