"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NavAuthButton } from "@/components/NavAuthButton";

const navigation = [
  { href: "/match", label: "Match" },
  { href: "/advisor", label: "AI advisor" },
  { href: "/application", label: "Application" },
  { href: "/applications", label: "My Tracker" }
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-quiet bg-paper/95 backdrop-blur-sm">
      <div className="site-container flex min-h-20 items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-3" aria-label="AUSA home" onClick={() => setOpen(false)}>
          <span className="flex h-10 w-10 items-center justify-center border border-ink font-serif text-xl font-semibold">A</span>
          <span>
            <span className="block font-serif text-xl font-semibold leading-none">AUSA</span>
            <span className="mt-1 block text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-muted">University advisor</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {navigation.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(`${item.href}`));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`min-h-11 border-b-2 px-4 py-3 text-sm font-semibold transition-colors ${
                  active ? "border-accent text-ink" : "border-transparent text-muted hover:border-line hover:text-ink"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden lg:block">
          <NavAuthButton />
        </div>

        <button
          type="button"
          className="flex h-11 w-11 items-center justify-center border border-ink lg:hidden"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          aria-controls="mobile-navigation"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
      </div>

      {open && (
        <div id="mobile-navigation" className="border-t border-quiet bg-paper lg:hidden">
          <div className="site-container py-5">
            <nav className="flex flex-col" aria-label="Mobile navigation">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="border-b border-quiet py-4 text-base font-semibold"
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
