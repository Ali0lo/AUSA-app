import type { Metadata } from "next";
import { FinanceSimulator } from "@/components/FinanceSimulator";

export const metadata: Metadata = {
  title: "Visa, Blocked Account & Living Cost Simulator · AUSA",
  description:
    "Statutory proof-of-funds calculations for Germany (§ 16b Sperrkonto), UK CAS 28-day maintenance, US Form I-20 COA, and Italy ISEE-U/DSU regional scholarships with real-time multi-currency conversion to Azerbaijani Manat (AZN).",
};

export default function FinancePage() {
  return (
    <div className="app-page">
      <FinanceSimulator />
    </div>
  );
}
