import type { Metadata } from "next";
import { TargetAnalyzer } from "@/components/TargetAnalyzer";

export const metadata: Metadata = {
  title: "Target University Gap Analysis · AUSA",
  description:
    "Evaluate your qualifications against a specific institution's published admissions criteria. Objective gap analysis, requirement checklists, and viable alternatives without speculative admission probabilities."
};

export default function TargetPage() {
  return (
    <div className="app-page">
      <div className="max-w-3xl">
        <p className="eyebrow">Target analysis</p>
        <h1 className="page-heading mt-3">Target University Gap Assessment</h1>
        <p className="body-large mt-6">
          Evaluate your academic credentials against a specific institution&apos;s published admissions
          criteria. View objective gap statements, multi-scale requirement checklists, process
          milestones, and viable alternatives that close the gap.
        </p>
        <p className="mt-4 text-sm leading-6 text-muted">
          All criteria are verified against primary institutional sources. Uncurated institutions
          honestly state data gaps rather than fabricating requirements, and speculative study plans
          are intentionally excluded.
        </p>
      </div>

      <div className="mt-10 sm:mt-14">
        <TargetAnalyzer />
      </div>
    </div>
  );
}
