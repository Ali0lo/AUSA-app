import type { Metadata } from "next";
import { SopChecker } from "@/components/SopChecker";

export const metadata: Metadata = {
  title: "SOP & Academic CV Rubric Checker · AUSA",
  description:
    "Evaluate your Statement of Purpose (SOP) and academic CV against top admissions rubrics, State Programme criteria, Chevening leadership rules, cliché pattern detectors, and readability metrics.",
};

export default function SopCheckerPage() {
  return (
    <div className="app-page">
      <SopChecker />
    </div>
  );
}
