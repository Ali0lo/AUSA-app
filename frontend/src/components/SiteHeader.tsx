"use client";

import { ChevronDown, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NavAuthButton } from "@/components/NavAuthButton";
import { languageLabels, useLanguage, type Language } from "@/lib/i18n";

const navigation = [
  // First, and deliberately. This is the surface backed by the real route engine and real
  // curated requirements, and since the weighted-score prototype was deleted it is also
  // the only place a student gets an answer about universities.
  { href: "/plan", label: "plan" },
  { href: "/target", label: "target" },
  { href: "/dashboard", label: "applications" },
  { href: "/finance", label: "finance" },
  { href: "/scholarships", label: "scholarships" },
  { href: "/dim-calculator", label: "dimCalculator" },
  { href: "/sop-checker", label: "sopChecker" },
  { href: "/timeline", label: "timeline" },
  { href: "/azerbaijan", label: "azerbaijan" },
  { href: "/advisor", label: "advisor" },
  { href: "/application", label: "application" },
  { href: "/applications", label: "applications" }
];

const desktopNavigation = navigation.filter((item) => ["plan", "target", "azerbaijan", "advisor"].includes(item.label));
const moreNavigation = navigation.filter((item) => !desktopNavigation.includes(item));

export function SiteHeader() {
  const { language, setLanguage, t } = useLanguage();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-[#0c0d1b]/80 backdrop-blur-xl transition-all">
      <div className="site-container flex min-h-20 items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-3 group" aria-label="AUSA home" onClick={() => setOpen(false)}>
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-gradient-to-br from-purple-500/20 via-pink-500/10 to-orange-500/20 font-sans text-xl font-extrabold text-white shadow-inner transition-transform group-hover:scale-105">
            A
          </span>
          <span>
            <span className="block font-sans text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent leading-none">
              AUSA
            </span>
            <span className="mt-1 block text-[0.62rem] font-semibold uppercase tracking-[0.16em] bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
              {t("universityAdvisor")}
            </span>
          </span>
        </Link>

        <nav className="hidden min-w-0 items-center gap-1 lg:flex" aria-label="Primary navigation">
          {desktopNavigation.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(`${item.href}`));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative min-h-11 px-4 py-3 text-sm font-medium transition-all ${
                  active
                    ? "text-white font-semibold"
                    : "text-slate-400 hover:text-white"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {t(item.label as Parameters<typeof t>[0])}
                {active && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 shadow-[0_0_8px_rgba(255,122,0,0.5)] animate-fade-in" />
                )}
              </Link>
            );
          })}
          <div className="relative">
            <button type="button" className="relative inline-flex min-h-11 items-center gap-1 px-4 py-3 text-sm font-medium text-slate-400 transition-colors hover:text-white" aria-expanded={moreOpen} onClick={() => setMoreOpen((value) => !value)}>
              {t("more")} <ChevronDown size={15} className={moreOpen ? "rotate-180 transition-transform" : "transition-transform"} aria-hidden="true" />
            </button>
            {moreOpen && (
              <div className="absolute right-0 top-full z-50 mt-2 min-w-56 rounded-2xl border border-white/10 bg-[#13152c] p-2 shadow-2xl backdrop-blur-xl">
                {moreNavigation.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return <Link key={item.href} href={item.href} onClick={() => setMoreOpen(false)} className={`block rounded-xl px-3 py-2.5 text-sm ${active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}>{t(item.label as Parameters<typeof t>[0])}</Link>;
                })}
              </div>
            )}
          </div>
        </nav>

        <div className="hidden lg:block">
          <NavAuthButton />
        </div>

        <div className="hidden items-center gap-1 rounded-xl border border-white/10 bg-white/[0.05] p-1 lg:flex" aria-label={t("language")}>
          {(Object.keys(languageLabels) as Language[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setLanguage(option)}
              className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors ${language === option ? "bg-white/15 text-white" : "text-slate-400 hover:text-white"}`}
              aria-pressed={language === option}
            >
              {languageLabels[option]}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] text-white hover:bg-white/10 transition-transform active:scale-95 lg:hidden"
          aria-label={open ? t("closeNavigation") : t("openNavigation")}
          aria-expanded={open}
          aria-controls="mobile-navigation"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X aria-hidden="true" size={20} /> : <Menu aria-hidden="true" size={20} />}
        </button>
      </div>

      {open && (
        <div id="mobile-navigation" className="animate-slide-down border-t border-white/[0.08] bg-[#0c0d1b]/95 backdrop-blur-2xl lg:hidden">
          <div className="site-container py-5">
            <nav className="flex flex-col" aria-label="Mobile navigation">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="border-b border-white/[0.06] py-3.5 text-base font-medium text-slate-200 hover:text-white"
                  onClick={() => setOpen(false)}
                >
                  {t(item.label as Parameters<typeof t>[0])}
                </Link>
              ))}
            </nav>
            <div className="mt-5 flex items-center gap-2" aria-label={t("language")}>
              {(Object.keys(languageLabels) as Language[]).map((option) => (
                <button key={option} type="button" onClick={() => setLanguage(option)} className={`rounded-lg border px-3 py-2 text-xs font-semibold ${language === option ? "border-orange-400 text-white" : "border-white/10 text-slate-400"}`} aria-pressed={language === option}>{languageLabels[option]}</button>
              ))}
            </div>
            <div className="mt-5">
              <NavAuthButton mobile />
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
