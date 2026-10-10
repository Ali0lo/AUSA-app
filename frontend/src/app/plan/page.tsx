"use client";

import { RoutePlanner } from "@/components/RoutePlanner";
import { useLanguage } from "@/lib/i18n";

export default function PlanPage() {
  const { t } = useLanguage();

  return (
    <div className="app-page">
      <div className="max-w-3xl">
        <p className="eyebrow">{t("routePlanning")}</p>
        <h1 className="page-heading mt-3">{t("planPageHeading")}</h1>
        <p className="body-large mt-5">{t("planPageBody")}</p>
        <p className="mt-3 text-sm leading-6 text-slate-400">{t("planPageNote")}</p>
      </div>

      <div className="mt-10 sm:mt-14">
        <RoutePlanner />
      </div>
    </div>
  );
}
