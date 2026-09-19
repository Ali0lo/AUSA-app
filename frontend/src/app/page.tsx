import { ArrowRight, BookOpenText, FileCheck2, Route } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { FeatureTag } from "@/components/FeatureTag";

const capabilities = [
  {
    title: "Route planning",
    description: "Enter your qualification and scores and see every route open to you, what each costs in time and money, and the universities that document accepting it — each quoted from its own admissions page.",
    href: "/plan",
    state: "available" as const,
    icon: Route
  },
  {
    title: "Grounded AI advisor",
    description: "Ask questions against the university-document retrieval endpoint and inspect every source returned with the answer.",
    href: "/advisor",
    state: "experimental" as const,
    icon: BookOpenText
  },
  {
    title: "Application assistant",
    description: "Exercise the current agent workflow, document checklist, application stage, and motivation-letter demonstration.",
    href: "/application",
    state: "demo" as const,
    icon: FileCheck2
  }
];

const team = ["Fariz Əkbərzadə", "Əli İskəndərli", "Turan Əlizadə", "Irada Nuraliyeva"];

export default function HomePage() {
  return (
    <>
      <section className="relative isolate min-h-[700px] overflow-hidden bg-[#0c0d1b] text-white">
        <Image
          src="/ausa-library-hero.jpg"
          alt="Students studying inside a university library in Zürich"
          fill
          priority
          sizes="100vw"
          className="-z-20 object-cover object-center opacity-30 brightness-75"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[#0c0d1b]/60 via-[#0c0d1b]/80 to-[#0c0d1b]" />
        
        {/* Ambient luminous glow in hero */}
        <div className="pointer-events-none absolute top-1/4 left-1/2 -translate-x-1/2 -z-10 h-[450px] w-[750px] rounded-full bg-gradient-to-r from-purple-600/20 via-pink-600/15 to-orange-500/15 blur-3xl animate-float-slow" />

        <div className="site-container flex min-h-[700px] items-center py-20">
          <div className="max-w-4xl">
            <div className="flex flex-wrap items-center gap-3 animate-fade-in">
              <span className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-orange-300 backdrop-blur-md shadow-sm">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-orange-500" />
                </span>
                AUSA prototype
              </span>
              <span className="text-sm font-medium text-slate-300">Built for Azerbaijani students</span>
            </div>
            
            <h1 className="mt-8 max-w-3xl font-sans text-5xl font-extrabold leading-[1.05] tracking-[-0.035em] text-white sm:text-6xl lg:text-7xl animate-slide-up">
              A clearer route to the{" "}
              <span className="bg-gradient-to-r from-purple-300 via-pink-300 to-orange-400 bg-clip-text text-transparent">
                right programme.
              </span>
            </h1>
            
            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl animate-slide-up animate-stagger-1">
              Enter what you hold and what you scored. See every route it opens, what each costs in time and money, and the universities that document accepting it — quoted from their own admissions pages.
            </p>
            
            <div className="mt-9 flex flex-wrap items-center gap-4 sm:gap-5 animate-slide-up animate-stagger-2">
              <Link className="button-primary min-h-14 px-8 text-base shadow-[0_0_25px_rgba(255,107,0,0.35)] interactive-scale" href="/plan">
                Plan my route
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link className="button-secondary min-h-14 px-7 text-base interactive-scale" href="/target">
                Target University
              </Link>
              <span className="text-sm text-slate-400">Free, and no account needed.</span>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-white/[0.08] py-16 sm:py-24" aria-labelledby="capabilities-heading">
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.4fr]">
            <div>
              <p className="eyebrow">Current build</p>
              <h2 id="capabilities-heading" className="section-heading mt-3">Working surfaces, clearly labelled.</h2>
              <p className="mt-5 max-w-md text-base leading-7 text-slate-400">
                Every area below maps to an endpoint or workflow already present in the repository. Demo and experimental states are shown openly.
              </p>
            </div>
            <div className="flex flex-col gap-4">
              {capabilities.map((capability) => {
                const Icon = capability.icon;
                return (
                  <article
                    key={capability.href}
                    className="group card-hover rounded-3xl border border-white/[0.08] bg-[#13152c]/75 p-6 backdrop-blur-xl shadow-xl sm:grid sm:grid-cols-[auto_1fr_auto] sm:items-center sm:gap-6"
                  >
                    <div className="mb-4 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-orange-400 transition-transform duration-300 group-hover:scale-110 group-hover:border-purple-500/30 group-hover:text-orange-300 sm:mb-0">
                      <Icon size={24} strokeWidth={1.75} aria-hidden="true" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="font-sans text-xl font-bold text-white">{capability.title}</h3>
                        <FeatureTag state={capability.state} />
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-400">{capability.description}</p>
                    </div>
                    <Link className="button-secondary mt-4 shrink-0 sm:mt-0 interactive-scale" href={capability.href}>
                      Open
                      <ArrowRight size={16} aria-hidden="true" />
                    </Link>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section id="method" className="scroll-mt-24 border-b border-white/[0.08] py-16 sm:py-24" aria-labelledby="method-heading">
        <div className="site-container">
          <div className="max-w-2xl">
            <p className="eyebrow">How it works</p>
            <h2 id="method-heading" className="section-heading mt-3">A short, inspectable path from profile to explanation.</h2>
          </div>
          <ol className="mt-12 grid gap-6 md:grid-cols-3">
            {[
              ["01", "Enter your profile", "Provide the GPA, language result, budget, target degree, and study field used by the existing matching request."],
              ["02", "Choose a demo programme", "Select one of the three programme records already used by the original frontend and backend demonstration."],
              ["03", "Inspect the response", "See eligibility, the prototype percentage, every factor score, and the backend's explanation without added claims."]
            ].map(([number, title, description]) => (
              <li
                key={number}
                className="card-hover rounded-3xl border border-white/[0.08] bg-[#13152c]/60 p-8 backdrop-blur-xl shadow-xl"
              >
                <span className="font-sans text-4xl font-extrabold bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
                  {number}
                </span>
                <h3 className="mt-5 font-sans text-xl font-bold text-white">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
              </li>
            ))}
          </ol>
          <div className="mt-10">
            <Link className="button-primary px-7 text-base shadow-[0_0_20px_rgba(255,107,0,0.3)] interactive-scale" href="/plan">
              Plan my route
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <section className="border-b border-white/[0.08] py-16 sm:py-20" aria-labelledby="trust-heading">
        <div className="site-container grid gap-10 lg:grid-cols-2 lg:gap-20">
          <div>
            <p className="eyebrow">Transparent by design</p>
            <h2 id="trust-heading" className="section-heading mt-3">The interface never disguises a missing service as a result.</h2>
          </div>
          <div className="space-y-6 text-base leading-7 text-slate-300">
            <p>Prototype scores are identified as prototype scores. Demo programme records are identified as demo data. AI answers retain the sources returned by retrieval.</p>
            <p>If the backend is offline, an endpoint is absent, a session has expired, or a request times out, the responsible page states that directly and keeps the rest of the interface usable.</p>
          </div>
        </div>
      </section>

      <section id="about" className="scroll-mt-24 py-16 sm:py-24" aria-labelledby="about-heading">
        <div className="site-container grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-20">
          <div>
            <p className="eyebrow">About AUSA</p>
            <h2 id="about-heading" className="section-heading mt-3">University guidance that explains its limits.</h2>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              AUSA is an evolving university and scholarship advisory platform. This frontend concentrates on the capabilities already represented in the repository while the catalogue, data, and models continue to develop.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-[#13152c]/85 p-6 backdrop-blur-2xl shadow-2xl sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
              Project team
            </p>
            <ul className="mt-5 divide-y divide-white/[0.08] border-y border-white/[0.08]">
              {team.map((member) => (
                <li key={member} className="py-3.5 text-sm font-medium text-slate-200">{member}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}
