import type { Metadata } from "next";
import { ScholarshipExplorer } from "@/components/ScholarshipExplorer";

export const metadata: Metadata = {
  title: "Global & Bilateral Scholarships Hub · AUSA",
  description:
    "Explore 14 official global scholarship programmes accessible to Azerbaijani students: Chevening, Fulbright, Türkiye Bursları, Stipendium Hungaricum, Italian DSU, DAAD, Eiffel France, NAWA Poland, and the State Programme 2022-2026.",
};

export default function ScholarshipsPage() {
  return (
    <div className="app-page">
      <ScholarshipExplorer />
    </div>
  );
}
