import type { Metadata } from "next";
import Link from "next/link";
import { AuthProvider } from "@/components/AuthProvider";
import { NavAuthButton } from "@/components/NavAuthButton";
import "./globals.css";

export const metadata: Metadata = {
  title: "AUSA Matching Platform",
  description: "AI-Powered University & Scholarship Matching Platform for Azerbaijani Students",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-slate-50 text-slate-900 min-h-screen flex flex-col">
        <AuthProvider>
          {/* Sleek Dark Blue Navigation Bar (bg-blue-900) */}
          <header className="bg-blue-900 text-white shadow-md border-b border-blue-800 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
              {/* Project Brand Title */}
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-lg text-white shadow-inner border border-blue-500">
                  A
                </div>
                <Link href="/" className="group">
                  <span className="font-extrabold text-xl tracking-tight text-white group-hover:text-blue-200 transition-colors">
                    AUSA Matching Platform
                  </span>
                  <span className="text-[10px] text-blue-200 block font-medium tracking-wide uppercase">
                    AI University & Scholarship Advisor
                  </span>
                </Link>
              </div>

              {/* Top Navigation Links & Auth Buttons */}
              <div className="flex items-center gap-4">
                <nav className="flex items-center gap-1">
                  <Link
                    href="/"
                    className="px-3 py-2 rounded-lg text-sm font-semibold text-blue-100 hover:text-white hover:bg-blue-800/80 transition-all"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/application"
                    className="px-3 py-2 rounded-lg text-sm font-semibold text-blue-100 hover:text-white hover:bg-blue-800/80 transition-all flex items-center gap-1.5"
                  >
                    <span>Application Assistant</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  </Link>
                </nav>

                <NavAuthButton />
              </div>
            </div>
          </header>

          {/* Page Children Content */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
            <div className="max-w-7xl mx-auto px-4">
              <p>AUSA Matching Platform — Azerbaijani Student Abroad Advisory © 2026</p>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
