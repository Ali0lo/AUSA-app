import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SOP & Academic CV Rubric Checker · AUSA",
  description:
    "Evaluate your Statement of Purpose (SOP) and academic CV against top admissions rubrics, State Programme criteria, Chevening leadership rules, cliché pattern detectors, and readability metrics.",
};

export default function SopCheckerLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}

