"use client";

import { useEffect, useState } from "react";
import { getAzerbaijanPredictions, type AzerbaijanPrediction, ApiError } from "@/lib/api";
import { ScrollReveal } from "@/components/ScrollReveal";

function verdict(row: AzerbaijanPrediction, score: number | null) {
  if (score === null) return null;
  const cutoff = row.predicted_cutoff ?? 650;
  const lower = row.lower_cutoff ?? 650;
  const upper = row.upper_cutoff ?? 700;
  if (score >= upper) return "clears";
  if (score >= cutoff) return "clears cutoff";
  if (score < lower) return "below";
  return "close";
}

const POPULAR_UNIVERSITIES = [
  { label: "All Universities", value: "" },
  { label: "Baku Higher Oil School (BHOS)", value: "bhos" },
  { label: "ADA University", value: "ada" },
  { label: "UNEC", value: "unec" },
  { label: "BDU", value: "bdu" },
];

export default function AzerbaijanPage() {
  const [university, setUniversity] = useState("");
  const [group, setGroup] = useState("");
  const [score, setScore] = useState("");
  const [rows, setRows] = useState<AzerbaijanPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const scoreValue = score === "" ? null : Number(score);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      getAzerbaijanPredictions({ university, group })
        .then((result) => {
          setRows(result.items);
          setError(null);
        })
        .catch((reason) => {
          setError(reason instanceof ApiError ? reason.message : "The Azerbaijan cutoff service is unavailable.");
        })
        .finally(() => setLoading(false));
    }, 200);
    return () => window.clearTimeout(timer);
  }, [university, group]);

  return (
    <div className="app-page">
      <ScrollReveal direction="down" duration={600}>
        <header className="max-w-3xl">
          <p className="eyebrow">Azerbaijan · DİM Admissions</p>
          <h1 className="page-heading mt-3">What may the next cutoff be?</h1>
          <p className="body-large mt-6">
            Predicts published DİM cutoffs for state-funded programmes at Azerbaijani universities from official
            cutoff history. For all full scholarships (dövlət sifarişli), the standard cutoff score is <strong>650+ DİM score</strong> if not specifically indicated by a competitive specialty.
          </p>
        </header>
      </ScrollReveal>

      {/* Full scholarship rule highlight notice */}
      <ScrollReveal direction="up" delay={100} duration={600}>
        <div className="mt-8 rounded-2xl border border-purple-500/30 bg-purple-950/20 p-5 backdrop-blur-md">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-xs font-bold text-purple-300">
              ★
            </span>
            <div className="text-sm">
              <span className="font-semibold text-purple-200">Full Scholarship Standard (Dövlət Sifarişli): </span>
              <span className="text-slate-300">
                At Baku Higher Oil School (BANM / BHOS) and partner universities, all full scholarships provide 100% tuition coverage plus monthly government stipends. Where a competitive cutoff is not indicated, the standard benchmark for full scholarship qualification is <strong>650+ points</strong> on the DİM entrance examination.
              </span>
            </div>
          </div>
        </div>
      </ScrollReveal>

      <ScrollReveal direction="up" delay={150} duration={600}>
        <section className="mt-8 border-y border-line py-7" aria-label="Filter Azerbaijan predictions">
          {/* Quick chips */}
          <div className="mb-5 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-400">Quick Filter:</span>
            {POPULAR_UNIVERSITIES.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => setUniversity(item.value)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  (university === item.value || (item.value === "bhos" && (university.toLowerCase().includes("oil") || university.toLowerCase().includes("banm"))))
                    ? "bg-[#FF7A00] text-white shadow-lg shadow-orange-500/20"
                    : "border border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            <label>
              <span className="field-label">University</span>
              <input
                className="field"
                value={university}
                onChange={(event) => setUniversity(event.target.value)}
                placeholder="Search a university (e.g. Baku Higher Oil School, ADA)"
              />
            </label>
            <label>
              <span className="field-label">DİM group</span>
              <select className="field" value={group} onChange={(event) => setGroup(event.target.value)}>
                <option value="">All groups</option>
                <option value="I qrup">Group 1</option>
                <option value="II qrup">Group 2</option>
                <option value="III qrup">Group 3</option>
                <option value="IV qrup">Group 4</option>
                <option value="V qrup">Group 5</option>
              </select>
            </label>
            <label>
              <span className="field-label">Your DİM score (optional)</span>
              <input
                className="field"
                type="number"
                min="0"
                max="700"
                value={score}
                onChange={(event) => setScore(event.target.value)}
                placeholder="0–700"
              />
            </label>
          </div>
          <p className="field-help mt-4">
            The band reflects the persistence and uncertainty interval. “Clears” means your score exceeds the projected cutoff range.
          </p>
        </section>
      </ScrollReveal>

      {error && <p className="notice notice-warning mt-8" role="alert">{error}</p>}
      
      {!error && !loading && rows.length === 0 && (
        <p className="notice notice-info mt-8">
          No Azerbaijan cutoff predictions are available matching your search. Try searching for “Baku Higher Oil School”, “BHOS”, or “ADA”.
        </p>
      )}

      <div className="mt-8 grid gap-4">
        {rows.map((row, idx) => {
          const state = verdict(row, Number.isFinite(scoreValue) ? scoreValue : null);
          const isBHOS = row.university_name?.toLowerCase().includes("oil") || row.university_name?.toLowerCase().includes("banm");
          const cutoffDisplay = row.predicted_cutoff != null
            ? `${row.predicted_cutoff.toFixed(1)} pts`
            : "650+ pts (Standard full scholarship)";

          return (
            <ScrollReveal key={row.program_code || idx} direction="up" delay={Math.min(idx * 40, 300)} duration={500}>
              <article className={`panel p-5 sm:p-6 transition-all hover:border-purple-500/40 ${isBHOS ? "border-purple-500/30 bg-white/[0.06]" : ""}`}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-serif text-2xl font-semibold text-white">
                        {row.department_name || "Unnamed programme"}
                      </h2>
                      <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-300">
                        {row.scholarship_type || "Dövlət Sifarişli (Full Scholarship)"}
                      </span>
                    </div>
                    <p className="mt-1 text-muted">
                      <span className="font-medium text-slate-200">{row.university_name}</span> · {row.score_type || "DİM score"}
                    </p>
                  </div>
                  {state && (
                    <span
                      className={`status-tag ${
                        state === "clears" || state === "clears cutoff"
                          ? "status-available"
                          : state === "below"
                          ? "status-offline"
                          : "status-experimental"
                      }`}
                    >
                      {state === "clears cutoff"
                        ? "clears cutoff"
                        : state === "close"
                        ? "too close to call"
                        : state}
                    </span>
                  )}
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-4 border-t border-white/5 pt-4">
                  <div>
                    <p className="eyebrow">Cutoff Score (Full Scholarship)</p>
                    <p className="mt-1 text-2xl font-bold bg-gradient-to-r from-purple-200 via-pink-200 to-orange-200 bg-clip-text text-transparent">
                      {cutoffDisplay}
                    </p>
                    {row.lower_cutoff != null && row.upper_cutoff != null && (
                      <p className="mt-0.5 text-xs text-slate-400">
                        Band: {row.lower_cutoff.toFixed(0)}–{row.upper_cutoff.toFixed(0)}
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="eyebrow">Projection Year</p>
                    <p className="mt-1 font-medium text-slate-200">{row.target_year || 2026}</p>
                    <p className="mt-0.5 text-xs text-slate-400">Upcoming intake</p>
                  </div>
                  <div>
                    <p className="eyebrow">Methodology</p>
                    <p className="mt-1 font-medium text-slate-200">{row.model || "Persistence"}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{row.prediction_type || "forecast"}</p>
                  </div>
                  <div>
                    <p className="eyebrow">Historical Data</p>
                    <p className="mt-1 font-medium text-slate-200">
                      {row.history_years ? `${row.history_years} intake years` : "Official standard"}
                    </p>
                    <p className="mt-0.5 text-xs text-purple-300/80">
                      {row.cutoff_note || "Full scholarship standard (650+)"}
                    </p>
                  </div>
                </div>
              </article>
            </ScrollReveal>
          );
        })}
      </div>
    </div>
  );
}