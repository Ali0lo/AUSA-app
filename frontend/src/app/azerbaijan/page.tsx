"use client";

import { useEffect, useState } from "react";
import { getAzerbaijanPredictions, type AzerbaijanPrediction, ApiError } from "@/lib/api";

function verdict(row: AzerbaijanPrediction, score: number | null) {
  if (score === null || row.lower_cutoff == null || row.upper_cutoff == null) return null;
  if (score >= row.upper_cutoff) return "clears";
  if (score < row.lower_cutoff) return "below";
  return "close";
}

export default function AzerbaijanPage() {
  const [university, setUniversity] = useState("");
  const [group, setGroup] = useState("");
  const [score, setScore] = useState("");
  const [rows, setRows] = useState<AzerbaijanPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const scoreValue = score === "" ? null : Number(score);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      getAzerbaijanPredictions({ university, group })
        .then((result) => { setRows(result.items); setError(null); })
        .catch((reason) => setError(reason instanceof ApiError ? reason.message : "The Azerbaijan cutoff service is unavailable."));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [university, group]);

  return (
    <div className="app-page">
      <header className="max-w-3xl">
        <p className="eyebrow">Azerbaijan · DİM</p>
        <h1 className="page-heading mt-3">What may the next cutoff be?</h1>
        <p className="body-large mt-6">
          This is a separate Azerbaijan section. It predicts the next published DİM cutoff for programmes at Azerbaijani universities from their cutoff history. It does not predict admission abroad, and it never uses your score as a model input.
        </p>
      </header>

      <section className="mt-12 border-y border-line py-7" aria-label="Filter Azerbaijan predictions">
        <div className="grid gap-5 md:grid-cols-3">
          <label><span className="field-label">University</span><input className="field" value={university} onChange={(event) => setUniversity(event.target.value)} placeholder="Search a university" /></label>
          <label><span className="field-label">DİM group</span><select className="field" value={group} onChange={(event) => setGroup(event.target.value)}><option value="">All groups</option><option value="I qrup">Group 1</option><option value="II qrup">Group 2</option><option value="III qrup">Group 3</option><option value="IV qrup">Group 4</option><option value="V qrup">Group 5</option></select></label>
          <label><span className="field-label">Your DİM score (optional)</span><input className="field" type="number" min="0" max="700" value={score} onChange={(event) => setScore(event.target.value)} placeholder="0–700" /></label>
        </div>
        <p className="field-help mt-4">The band is a range, not a promise. “Close” means your score falls inside the uncertainty interval.</p>
      </section>

      {error && <p className="notice notice-warning mt-8" role="alert">{error}</p>}
      {!error && rows.length === 0 && <p className="notice notice-info mt-8">No Azerbaijan cutoff predictions are available yet. This is a data or model absence, not a claim that no programme exists.</p>}
      <div className="mt-8 grid gap-4">
        {rows.map((row) => {
          const state = verdict(row, Number.isFinite(scoreValue) ? scoreValue : null);
          return <article className="panel p-5 sm:p-6" key={row.program_code}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div><h2 className="font-serif text-2xl font-semibold">{row.department_name || "Unnamed programme"}</h2><p className="mt-1 text-muted">{row.university_name} · {row.score_type || "DİM score"}</p></div>
              {state && <span className={`status-tag ${state === "clears" ? "status-available" : state === "below" ? "status-offline" : "status-experimental"}`}>{state === "close" ? "too close to call" : state}</span>}
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-3"><div><p className="eyebrow">Predicted {row.target_year}</p><p className="mt-1 text-2xl font-semibold">{row.lower_cutoff?.toFixed(0)}–{row.upper_cutoff?.toFixed(0)}</p></div><div><p className="eyebrow">Method</p><p className="mt-1">{row.model} · {row.prediction_type}</p></div><div><p className="eyebrow">History</p><p className="mt-1">{row.history_years} intake years</p></div></div>
          </article>;
        })}
      </div>
    </div>
  );
}