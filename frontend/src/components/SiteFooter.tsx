import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-white/[0.08] bg-[#090a15]/90 backdrop-blur-xl text-slate-300">
      <div className="site-container grid gap-10 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <p className="font-sans text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            AUSA
          </p>
          <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">
            A transparent university and application advisory prototype for Azerbaijani students.
          </p>
          <p className="mt-5 text-xs leading-5 text-slate-500">
            Prototype results are informational and are not admission or scholarship guarantees.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Product</p>
          <div className="mt-4 flex flex-col items-start gap-3 text-sm">
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/plan">Route planning</Link>
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/target">Target University</Link>
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/azerbaijan">Azerbaijan DİM cutoffs</Link>
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/advisor">AI advisor</Link>
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/application">Application assistant</Link>
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Information</p>
          <div className="mt-4 flex flex-col items-start gap-3 text-sm">
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/#method">How it works</Link>
            <Link className="text-slate-300 transition-colors hover:text-orange-400" href="/#about">About the project</Link>
            <a
              className="text-slate-300 transition-colors hover:text-orange-400"
              href="https://unsplash.com/photos/a-library-filled-with-lots-of-books-and-people-sitting-at-tables-gdZ9GPNi_VM"
              target="_blank"
              rel="noreferrer"
            >
              Hero photo credit
            </a>
          </div>
        </div>
      </div>
      <div className="border-t border-white/[0.06]">
        <div className="site-container flex flex-col gap-2 py-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>© 2026 AUSA team</span>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <span className="text-slate-400">All systems operational</span>
          </div>
          <span>Frontend build 1.0 · English interface</span>
        </div>
      </div>
    </footer>
  );
}
