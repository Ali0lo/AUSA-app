import { ArrowRight, BookOpenText, FileCheck2, Scale } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { FeatureTag } from "@/components/FeatureTag";
import { LandingSearch } from "@/components/LandingSearch";

const capabilities = [
  {
    title: "Prototype matching",
    description: "Enter a student profile, select one of the existing demo programmes, and receive the backend's current compatibility breakdown.",
    href: "/match",
    state: "demo" as const,
    icon: Scale
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

const team = ["Irada Nuraliyeva", "Əli İskəndərli", "Fariz Əkbərzadə", "Turan Əlizadə"];

export default function HomePage() {
  return (
    <>
      <section className="relative isolate min-h-[680px] overflow-hidden bg-ink text-paper">
        <Image
          src="/ausa-library-hero.jpg"
          alt="Students studying inside a university library in Zürich"
          fill
          priority
          sizes="100vw"
          className="-z-20 object-cover object-center"
        />
        <div className="absolute inset-0 -z-10 bg-[#171916d9]" />
        <div className="site-container flex min-h-[680px] items-center py-20">
          <div className="max-w-4xl">
            <div className="flex flex-wrap items-center gap-3">
              <span className="border border-[#e5a27e] px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-[#f1c5ae]">AUSA prototype</span>
              <span className="text-sm text-[#deddd8]">Built for Azerbaijani students</span>
            </div>
            <h1 className="mt-8 max-w-3xl font-serif text-5xl font-semibold leading-[0.98] tracking-[-0.035em] sm:text-6xl lg:text-7xl">
              A clearer route to the right programme.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-[#deddd8] sm:text-xl">
              Compare a student profile with programme requirements, inspect the current prototype score, and prepare an application without hiding what the system can and cannot do.
            </p>
            <div className="mt-9">
              <LandingSearch />
            </div>
            <p className="mt-3 text-xs leading-5 text-[#c7c6c1]">
              Search covers three frontend demo programmes. Full catalogue search is not implemented by the current backend.
            </p>
          </div>
        </div>
      </section>

      <section className="border-b border-line bg-paper py-16 sm:py-20" aria-labelledby="capabilities-heading">
        <div className="site-container">
          <div className="grid gap-8 lg:grid-cols-[0.8fr_1.4fr]">
            <div>
              <p className="eyebrow">Current build</p>
              <h2 id="capabilities-heading" className="section-heading mt-3">Working surfaces, clearly labelled.</h2>
              <p className="mt-5 max-w-md leading-7 text-muted">
                Every area below maps to an endpoint or workflow already present in the repository. Demo and experimental states are shown openly.
              </p>
            </div>
            <div className="border-t border-line">
              {capabilities.map((capability) => {
                const Icon = capability.icon;
                return (
                  <article key={capability.href} className="grid gap-5 border-b border-quiet py-7 sm:grid-cols-[auto_1fr_auto] sm:items-start">
                    <Icon size={25} strokeWidth={1.5} className="mt-1 text-accent" aria-hidden="true" />
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="font-serif text-2xl font-semibold">{capability.title}</h3>
                        <FeatureTag state={capability.state} />
                      </div>
                      <p className="mt-3 max-w-2xl leading-7 text-muted">{capability.description}</p>
                    </div>
                    <Link className="button-secondary shrink-0" href={capability.href}>
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

      <section id="method" className="scroll-mt-24 py-16 sm:py-24" aria-labelledby="method-heading">
        <div className="site-container">
          <div className="max-w-2xl">
            <p className="eyebrow">How it works</p>
            <h2 id="method-heading" className="section-heading mt-3">A short, inspectable path from profile to explanation.</h2>
          </div>
          <ol className="mt-12 grid border-y border-line md:grid-cols-3">
            {[
              ["01", "Enter your profile", "Provide the GPA, language result, budget, target degree, and study field used by the existing matching request."],
              ["02", "Choose a demo programme", "Select one of the three programme records already used by the original frontend and backend demonstration."],
              ["03", "Inspect the response", "See eligibility, the prototype percentage, every factor score, and the backend's explanation without added claims."]
            ].map(([number, title, description], index) => (
              <li key={number} className={`py-8 md:px-8 ${index > 0 ? "border-t border-quiet md:border-l md:border-t-0" : ""}`}>
                <span className="font-serif text-4xl text-accent">{number}</span>
                <h3 className="mt-6 font-serif text-2xl font-semibold">{title}</h3>
                <p className="mt-3 leading-7 text-muted">{description}</p>
              </li>
            ))}
          </ol>
          <div className="mt-9">
            <Link className="button-primary" href="/match">
              Start prototype matching
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-paper py-16 sm:py-20" aria-labelledby="trust-heading">
        <div className="site-container grid gap-10 lg:grid-cols-2 lg:gap-20">
          <div>
            <p className="eyebrow">Transparent by design</p>
            <h2 id="trust-heading" className="section-heading mt-3">The interface never disguises a missing service as a result.</h2>
          </div>
          <div className="space-y-6 text-base leading-7 text-muted">
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
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">
              AUSA is an evolving university and scholarship advisory platform. This frontend concentrates on the capabilities already represented in the repository while the catalogue, data, and models continue to develop.
            </p>
          </div>
          <div className="panel-strong p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-accent">Project team</p>
            <ul className="mt-5 divide-y divide-quiet border-y border-quiet">
              {team.map((member) => (
                <li key={member} className="py-3.5 font-medium">{member}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}
