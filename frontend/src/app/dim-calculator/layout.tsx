import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DİM 700 Bal Kalkulyatoru və İxtisas Seçimi Bələdçisi · AUSA",
  description:
    "Dövlət İmtahan Mərkəzi (DİM) üzrə Buraxılış (300 bal) və Blok (400 bal) nəticələrinizi hesablayın, 2,578 rəsmi keçid balı əsasında şansınızı dəqiq müəyyənləşdirin.",
};

export default function DimCalculatorLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}

