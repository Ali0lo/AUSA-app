"use client";

import { DimScoreSimulator } from "@/components/DimScoreSimulator";
import { useLanguage } from "@/lib/i18n";

export default function DimCalculatorPage() {
  const { t } = useLanguage();

  return (
    <div className="app-page">
      <div className="mb-8 space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold text-orange-400 backdrop-blur-md">
          <span className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-pulse" />
          {t("dimCalcBadge")}
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
          {t("dimCalcHeading")}
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          {t("dimCalcSubtitle")}
        </p>
      </div>

      <DimScoreSimulator />
    </div>
  );
}
