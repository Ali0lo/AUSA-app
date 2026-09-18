import type { Metadata } from "next";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-serif/500.css";
import "@fontsource/ibm-plex-serif/600.css";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: {
    default: "AUSA · University Advisor",
    template: "%s · AUSA"
  },
  description: "A transparent university and application advisory prototype for Azerbaijani students."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className="dark">
      <body className="relative flex min-h-screen flex-col bg-[#0c0d1b] text-white selection:bg-orange-500/30 selection:text-white">
        {/* Ambient background glow layers */}
        <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute -top-40 left-1/2 h-[550px] w-[850px] -translate-x-1/2 rounded-full bg-gradient-to-b from-purple-600/15 via-pink-600/10 to-transparent blur-3xl" />
          <div className="absolute top-[35%] -right-24 h-[600px] w-[600px] rounded-full bg-violet-600/[0.08] blur-3xl" />
          <div className="absolute bottom-10 -left-24 h-[500px] w-[500px] rounded-full bg-orange-600/[0.06] blur-3xl" />
        </div>

        <AuthProvider>
          <a href="#main-content" className="skip-link">Skip to content</a>
          <SiteHeader />
          <main id="main-content" className="flex-1">{children}</main>
          <SiteFooter />
        </AuthProvider>
      </body>
    </html>
  );
}
