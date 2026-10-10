import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Target University Gap Analysis · AUSA",
  description:
    "Evaluate your qualifications against a specific institution's published admissions criteria. Objective gap analysis, requirement checklists, and viable alternatives without speculative admission probabilities."
};

export default function TargetLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}

