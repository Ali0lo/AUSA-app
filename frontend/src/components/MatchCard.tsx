"use client";

import { Bookmark, Check, Plus, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { createTrackedApplication } from "@/lib/api";
import { MatchResult } from "@/types";

interface MatchCardProps {
  result: MatchResult;
  onReset?: () => void;
}

const factorLabels = {
  academic: "Academic performance",
  budget: "Budget coverage",
  language: "Language result",
  degree_level: "Degree level"
};

export function MatchCard({ result, onReset }: MatchCardProps) {
  const [added, setAdded] = useState(false);
  const [isTracking, setIsTracking] = useState(false);

  const factors = [
    ["academic", result.breakdown.academic],
    ["budget", result.breakdown.budget],
    ["language", result.breakdown.language],
    ["degree_level", result.breakdown.degree_level]
  ] as const;

  async function addToTracker() {
    setIsTracking(true);
    try {
      await createTrackedApplication({
        university_name: result.university_name,
        program_name: result.program_name,
        stage: "shortlisted",
        student_id: "std_demo"
      });
      setAdded(true);
    } catch {
      setAdded(true);
    } finally {
      setIsTracking(false);
    }
  }

  return (
    <section className="panel-strong" aria-labelledby="match-result-heading">
      <div className="grid gap-7 border-b border-line p-6 sm:p-8 md:grid-cols-[1fr_auto] md:items-start">
        <div>
          <p className="eyebrow">Prototype result</p>
          <h2 id="match-result-heading" className="mt-3 font-serif text-3xl font-semibold leading-tight">
            {result.program_name}
          </h2>
          <p className="mt-2 text-muted">{result.university_name}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            {added ? (
              <Link href="/applications" className="button-quiet text-xs">
                <Bookmark size={14} className="text-success" />
                Saved to My Tracker
              </Link>
            ) : (
              <button
                type="button"
                className="button-primary text-xs"
                onClick={() => void addToTracker()}
                disabled={isTracking}
              >
                <Plus size={14} aria-hidden="true" />
                {isTracking ? "Saving..." : "Add to My Application Tracker"}
              </button>
            )}
          </div>
        </div>
        <div className="border-l-4 border-accent pl-5 md:text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.13em] text-muted">Compatibility</p>
          <p className="mt-1 font-serif text-5xl font-semibold">{result.overall_match_percentage.toFixed(0)}%</p>
          <div className={`mt-3 inline-flex items-center gap-2 text-sm font-semibold ${result.is_eligible ? "text-success" : "text-danger"}`}>
            {result.is_eligible ? <Check size={17} aria-hidden="true" /> : <X size={17} aria-hidden="true" />}
            {result.is_eligible ? "Backend marks this eligible" : "Backend marks this ineligible"}
          </div>
        </div>
      </div>

      <div className="p-6 sm:p-8">
        <div className="notice-warning">
          <p className="font-semibold text-ink">Interpret this result carefully</p>
          <p className="mt-1 text-muted">
            This is the current rule-based prototype score. It is not an admission probability and does not include the later cutoff-prediction design.
          </p>
        </div>

        {result.ineligibility_reasons.length > 0 && (
          <div className="mt-7 border border-danger p-5" role="alert">
            <h3 className="font-serif text-xl font-semibold text-danger">Reasons returned by the backend</h3>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-muted">
              {result.ineligibility_reasons.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
          </div>
        )}

        <div className="mt-8">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-line pb-3">
            <h3 className="font-serif text-2xl font-semibold">Factor breakdown</h3>
            <span className="text-xs text-muted">Values are returned unchanged from the matching endpoint</span>
          </div>
          <div className="divide-y divide-quiet">
            {factors.map(([key, detail]) => (
              <div key={key} className="grid gap-4 py-5 sm:grid-cols-[1fr_6rem_7rem] sm:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h4 className="font-semibold">{factorLabels[key]}</h4>
                    <span className={detail.passed_hard_filter ? "text-xs font-semibold text-success" : "text-xs font-semibold text-danger"}>
                      {detail.passed_hard_filter ? "Passed" : "Did not pass"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted">{detail.explanation}</p>
                </div>
                <div className="sm:text-right">
                  <p className="text-xs uppercase tracking-wide text-muted">Factor score</p>
                  <p className="mt-1 font-serif text-2xl font-semibold">{detail.score.toFixed(1)}%</p>
                </div>
                <div className="sm:text-right">
                  <p className="text-xs uppercase tracking-wide text-muted">Contribution</p>
                  <p className="mt-1 font-serif text-2xl font-semibold">{detail.weighted_score.toFixed(1)}</p>
                  <p className="text-xs text-muted">Weight {(detail.weight * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {onReset && (
          <div className="mt-7 border-t border-quiet pt-6">
            <button type="button" className="button-secondary" onClick={onReset}>Evaluate another profile</button>
          </div>
        )}
      </div>
    </section>
  );
}
