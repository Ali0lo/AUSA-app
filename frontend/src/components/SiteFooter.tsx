import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-ink text-paper">
      <div className="site-container grid gap-10 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <p className="font-serif text-2xl font-semibold">AUSA</p>
          <p className="mt-3 max-w-md text-sm leading-6 text-[#d8d7d2]">
            A transparent university and application advisory prototype for Azerbaijani students.
          </p>
          <p className="mt-5 text-xs leading-5 text-[#bdbdb7]">
            Prototype results are informational and are not admission or scholarship guarantees.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#d8d7d2]">Product</p>
          <div className="mt-4 flex flex-col items-start gap-3 text-sm">
            <Link className="hover:text-[#e5a27e]" href="/plan">Route planning</Link>
            <Link className="hover:text-[#e5a27e]" href="/advisor">AI advisor</Link>
            <Link className="hover:text-[#e5a27e]" href="/application">Application assistant</Link>
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#d8d7d2]">Information</p>
          <div className="mt-4 flex flex-col items-start gap-3 text-sm">
            <Link className="hover:text-[#e5a27e]" href="/#method">How it works</Link>
            <Link className="hover:text-[#e5a27e]" href="/#about">About the project</Link>
            <a
              className="hover:text-[#e5a27e]"
              href="https://unsplash.com/photos/a-library-filled-with-lots-of-books-and-people-sitting-at-tables-gdZ9GPNi_VM"
              target="_blank"
              rel="noreferrer"
            >
              Hero photo credit
            </a>
          </div>
        </div>
      </div>
      <div className="border-t border-[#4d504b]">
        <div className="site-container flex flex-col gap-2 py-5 text-xs text-[#bdbdb7] sm:flex-row sm:items-center sm:justify-between">
          <span>© 2026 AUSA team</span>
          <span>Frontend build 1.0 · English interface</span>
        </div>
      </div>
    </footer>
  );
}
