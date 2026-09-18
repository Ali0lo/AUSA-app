import type { Metadata } from "next";
import { RoutePlanner } from "@/components/RoutePlanner";

export const metadata: Metadata = {
  title: "Plan your route · AUSA",
  description:
    "Enter your qualification and scores and see every route open to you, what each costs in time and money, and which universities document accepting it."
};

export default function PlanPage() {
  return (
    <div className="app-page">
      <div className="max-w-3xl">
        <p className="eyebrow">Route planning</p>
        <h1 className="page-heading mt-3">Every option your results actually open.</h1>
        <p className="body-large mt-5">
          Not a shortlist of what we would recommend. Every route that your qualification and
          scores make reachable, ranked by how long it takes, with the universities that
          document accepting what each route gives you.
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Requirements are quoted from each university&apos;s own admissions page and linked back
          to it. Where a page does not state something, it is shown as not stated rather than
          left blank — an unknown requirement is not an absent one.
        </p>
      </div>

      <div className="mt-10 sm:mt-14">
        <RoutePlanner />
      </div>
    </div>
  );
}
