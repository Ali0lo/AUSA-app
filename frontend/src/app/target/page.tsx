"use client";

import { TargetAnalyzer } from "@/components/TargetAnalyzer";
import { useLanguage } from "@/lib/i18n";

export default function TargetPage() {
  const { t } = useLanguage();

  return (
    <div className="app-page">
      <div className="max-w-3xl">
        <p className="eyebrow">{t("targetUniversity")}</p>
        <h1 className="page-heading mt-3">
          {t("targetRoadmap", "Target University Gap Assessment")}
        </h1>
        <p className="body-large mt-5">
          {t(
            "targetUniBody",
            "Evaluate your academic credentials against a specific institution's published admissions criteria. View objective gap statements, multi-scale requirement checklists, process milestones, and viable alternatives that close the gap."
          )}
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          {t(
            "targetUniNote",
            "All criteria are verified against primary institutional sources. Uncurated institutions honestly state data gaps rather than fabricating requirements, and speculative study plans are intentionally excluded."
          )}
        </p>
      </div>

      <div className="mt-10 sm:mt-14">
        <TargetAnalyzer />
      </div>
    </div>
  );
}
