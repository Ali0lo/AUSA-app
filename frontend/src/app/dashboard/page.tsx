import type { Metadata } from "next";
import { ApplicationDashboard } from "@/components/ApplicationDashboard";

export const metadata: Metadata = {
  title: "Tətbiq Paneli & Universitet Müqayisəsi · AUSA",
  description:
    "Xəyal, hədəf və təhlükəsiz universitet seçimlərinizi izləyin, tələb olunan sənədlərin yoxlama siyahısını idarə edin və qəbul şansınızı sistemli şəkildə artırın.",
};

export default function DashboardPage() {
  return (
    <div className="app-page">
      <ApplicationDashboard />
    </div>
  );
}
