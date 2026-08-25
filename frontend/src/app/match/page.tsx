import type { Metadata } from "next";
import { Suspense } from "react";
import { MatchWorkspace } from "@/components/MatchWorkspace";

export const metadata: Metadata = {
  title: "Prototype matching",
  description: "Compare a student profile with the current AUSA programme-matching backend."
};

export default function MatchPage() {
  return (
    <Suspense fallback={<div className="app-page"><p role="status">Preparing the matching workspace</p></div>}>
      <MatchWorkspace />
    </Suspense>
  );
}
