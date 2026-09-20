"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NavAuthButton } from "@/components/NavAuthButton";

const navigation = [
  // First, and deliberately. This is the surface backed by the real route engine and real
  // curated requirements, and since the weighted-score prototype was deleted it is also
  // the only place a student gets an answer about universities.
  { href: "/plan", label: "Plan my route" },
  { href: "/target", label: "Target University" },
  { href: "/finance", label: "Finances & Visa" },
  { href: "/scholarships", label: "Scholarships" },
  { href: "/azerbaijan", label: "Azerbaijan DİM" },
  { href: "/advisor", label: "AI advisor" },
  { href: "/application", label: "Application" },
  { href: "/applications", label: "My Tracker" }
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
              University advisor
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {navigation.map((item) => {
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
                {item.label}
                {active && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 shadow-[0_0_8px_rgba(255,122,0,0.5)] animate-fade-in" />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="hidden lg:block">
          <NavAuthButton />
        </div>

        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] text-white hover:bg-white/10 transition-transform active:scale-95 lg:hidden"
          aria-label={open ? "Close navigation" : "Open navigation"}
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
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="mt-5">
              <NavAuthButton mobile />
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
