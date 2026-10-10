import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Admissions Timeline & Calendar · AUSA",
  description:
    "Track verified application deadlines and admissions milestones for 2026/2027: UK UCAS, Germany Uni-Assist, US Common App, Azerbaijan State Programme, Türkiye Bursları, and Italian DSU with one-click .ics calendar synchronization.",
};

export default function TimelineLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}

