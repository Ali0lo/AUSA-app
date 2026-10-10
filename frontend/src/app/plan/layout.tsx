import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Plan your route · AUSA",
  description:
    "Enter your qualification and scores and see every route open to you, what each costs in time and money, and which universities document accepting it."
};

export default function PlanLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}

