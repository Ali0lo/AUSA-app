"use client";

import { ArrowRight, BookOpenText, FileCheck2, LineChart, Route } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { FeatureTag } from "@/components/FeatureTag";
import { ScrollReveal } from "@/components/ScrollReveal";
import { useLanguage, type TranslationKey } from "@/lib/i18n";

interface CapabilityItem {
  titleKey: TranslationKey;
  descKey: TranslationKey;
  href: string;
  state: "available" | "experimental" | "demo";
  icon: typeof Route;
}

const capabilities: CapabilityItem[] = [
  {
    titleKey: "routePlanning",
    descKey: "routePlanningDesc",
    href: "/plan",
    state: "available",
    icon: Route
  },
  {
    titleKey: "aiAdvisor",
    descKey: "aiAdvisorDesc",
    href: "/advisor",
    state: "experimental",
    icon: BookOpenText
  },
  {
    titleKey: "azerbaijan",
    descKey: "azerbaijanDescription",
    href: "/azerbaijan",
    state: "available",
    icon: LineChart
  },
  {
    titleKey: "applicationAssistant",
    descKey: "applicationAssistantDesc",
    href: "/application",
    state: "demo",
    icon: FileCheck2
  }
];

const team = ["Fariz Əkbərzadə", "Əli İskəndərli", "Turan Əlizadə", "Irada Nuraliyeva"];

export default function HomePage() {
  const { t } = useLanguage();

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
                {t("prototypeBadge")}
              </span>
              <span className="text-sm font-medium text-slate-300">{t("builtForAzerbaijani")}</span>
            </div>

            <h1 className="mt-8 max-w-3xl font-sans text-5xl font-extrabold leading-[1.05] tracking-[-0.035em] text-white sm:text-6xl lg:text-7xl animate-slide-up">
              {t("heroHeading")}{" "}
              <span className="bg-gradient-to-r from-purple-300 via-pink-300 to-orange-400 bg-clip-text text-transparent">
                {t("heroHeadingHighlight")}
              </span>
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl animate-slide-up animate-stagger-1">
              {t("heroSubtitle")}
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4 sm:gap-5 animate-slide-up animate-stagger-2">
              <Link className="button-primary min-h-14 px-8 text-base shadow-[0_0_25px_rgba(255,107,0,0.35)] interactive-scale" href="/plan">
                {t("plan")}
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link className="button-secondary min-h-14 px-7 text-base interactive-scale" href="/target">
                {t("target")}
              </Link>
              <span className="text-sm text-slate-400">{t("freeNoAccount")}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-white/[0.08] py-16 sm:py-24" aria-labelledby="capabilities-heading">
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.4fr]">
            <ScrollReveal direction="up" distance={20}>
              <p className="eyebrow">{t("currentBuild")}</p>
              <h2 id="capabilities-heading" className="section-heading mt-3">{t("workingSurfaces")}</h2>
              <p className="mt-5 max-w-md text-base leading-7 text-slate-400">
                {t("workingSurfacesDesc")}
              </p>
            </ScrollReveal>
            <div className="flex flex-col gap-4">
              {capabilities.map((capability, idx) => {
                const Icon = capability.icon;
                return (
                  <ScrollReveal key={capability.href} delay={idx * 100} direction="up" distance={24}>
                    <article className="group card-hover rounded-3xl border border-white/[0.08] bg-[#13152c]/75 p-6 backdrop-blur-xl shadow-xl sm:grid sm:grid-cols-[auto_1fr_auto] sm:items-center sm:gap-6">
                      <div className="mb-4 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-orange-400 transition-transform duration-300 group-hover:scale-110 group-hover:border-purple-500/30 group-hover:text-orange-300 sm:mb-0">
                        <Icon size={24} strokeWidth={1.75} aria-hidden="true" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="font-sans text-xl font-bold text-white">{t(capability.titleKey)}</h3>
                          <FeatureTag state={capability.state} />
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-400">{t(capability.descKey)}</p>
                      </div>
                      <Link className="button-secondary mt-4 shrink-0 sm:mt-0 interactive-scale" href={capability.href}>
                        {t("open")}
                        <ArrowRight size={16} aria-hidden="true" />
                      </Link>
                    </article>
                  </ScrollReveal>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section id="method" className="scroll-mt-24 border-b border-white/[0.08] py-16 sm:py-24" aria-labelledby="method-heading">
        <div className="site-container">
          <ScrollReveal direction="up">
            <div className="max-w-2xl">
              <p className="eyebrow">{t("howItWorks")}</p>
              <h2 id="method-heading" className="section-heading mt-3">{t("howItWorksHeading")}</h2>
            </div>
          </ScrollReveal>
          <ol className="mt-12 grid gap-6 md:grid-cols-3">
            {[
              ["01", t("step1Title"), t("step1Desc")],
              ["02", t("step2Title"), t("step2Desc")],
              ["03", t("step3Title"), t("step3Desc")]
            ].map(([number, title, description], idx) => (
              <ScrollReveal key={number} delay={idx * 120} direction="up" distance={30}>
                <li className="card-hover h-full rounded-3xl border border-white/[0.08] bg-[#13152c]/60 p-8 backdrop-blur-xl shadow-xl">
                  <span className="font-sans text-4xl font-extrabold bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
                    {number}
                  </span>
                  <h3 className="mt-5 font-sans text-xl font-bold text-white">{title}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
                </li>
              </ScrollReveal>
            ))}
          </ol>
          <ScrollReveal delay={350} direction="up">
            <div className="mt-10">
              <Link className="button-primary px-7 text-base shadow-[0_0_20px_rgba(255,107,0,0.3)] interactive-scale" href="/plan">
                {t("plan")}
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <section className="border-b border-white/[0.08] py-16 sm:py-20" aria-labelledby="trust-heading">
        <div className="site-container grid gap-10 lg:grid-cols-2 lg:gap-20">
          <ScrollReveal direction="left">
            <div>
              <p className="eyebrow">{t("transparentEyebrow")}</p>
              <h2 id="trust-heading" className="section-heading mt-3">{t("transparentHeading")}</h2>
            </div>
          </ScrollReveal>
          <ScrollReveal direction="right" delay={150}>
            <div className="space-y-6 text-base leading-7 text-slate-300">
              <p>{t("transparentP1")}</p>
              <p>{t("transparentP2")}</p>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <section id="about" className="scroll-mt-24 py-16 sm:py-24" aria-labelledby="about-heading">
        <div className="site-container grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-20">
          <ScrollReveal direction="up">
            <div>
              <p className="eyebrow">{t("aboutEyebrow")}</p>
              <h2 id="about-heading" className="section-heading mt-3">{t("aboutHeading")}</h2>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
                {t("aboutDesc")}
              </p>
            </div>
          </ScrollReveal>
          <ScrollReveal direction="up" delay={200} distance={32}>
            <div className="rounded-3xl border border-white/10 bg-[#13152c]/85 p-6 backdrop-blur-2xl shadow-2xl sm:p-8">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
                {t("projectTeam")}
              </p>
              <ul className="mt-5 divide-y divide-white/[0.08] border-y border-white/[0.08]">
                {team.map((member) => (
                  <li key={member} className="py-3.5 text-sm font-medium text-slate-200">{member}</li>
                ))}
              </ul>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </>
  );
}
