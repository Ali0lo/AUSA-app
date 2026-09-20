import type { Metadata } from "next";
import { DimScoreSimulator } from "@/components/DimScoreSimulator";

export const metadata: Metadata = {
  title: "DİM 700 Bal Kalkulyatoru və İxtisas Seçimi Bələdçisi · AUSA",
  description:
    "Dövlət İmtahan Mərkəzi (DİM) üzrə Buraxılış (300 bal) və Blok (400 bal) nəticələrinizi hesablayın, 2,578 rəsmi keçid balı əsasında şansınızı dəqiq müəyyənləşdirin.",
};

export default function DimCalculatorPage() {
  return (
    <div className="app-page">
      <div className="mb-8 space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold text-orange-400 backdrop-blur-md">
          <span className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-pulse" />
          Rəsmi DİM Qaydaları & 2023–2025 Keçid Balları
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
          DİM Sub-İmtahan Kalkulyatoru və İxtisas Seçimi
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Buraxılış və İxtisas bloku fənləri üzrə sual saylarınızı və ya dəqiq ballarınızı daxil edin.
          Sistem 4 səhvin 1 düzü aparması qaydası ilə balınızı hesablayır və 2,578 rəsmi dövlət sifarişli
          ixtisas üzrə qəbul şansınızı Safe, Realistic və Target kateqoriyalarına bölür.
        </p>
      </div>

      <DimScoreSimulator />
    </div>
  );
}
