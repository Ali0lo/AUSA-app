"use client";

import { useEffect, useState, useTransition } from "react";
import {
  assessTargetGap,
  fetchTargetCatalog,
  getUserFacingError
} from "@/lib/api";
import type {
  GradeScaleKey,
  RouteQualification,
  TargetCatalogItem,
  TargetGapPayload,
  TargetGapResponse
} from "@/types";
import {
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  GraduationCap,
  HelpCircle,
  RefreshCw,
  Search,
  Sparkles,
  XCircle
} from "lucide-react";

const GRADE_SCALES: { value: GradeScaleKey; label: string }[] = [
  { value: "5.0", label: "out of 5 — the usual attestat scale" },
  { value: "100", label: "out of 100 — most Azerbaijani and Turkish universities" },
  { value: "4.0", label: "out of 4.0 — US-style GPA" },
  { value: "german", label: "German 1.0–4.0 — where 1.0 is best" }
];

const COUNTRY_NAMES: Record<string, string> = {
  AZ: "Azerbaijan",
  TR: "Turkey",
  PL: "Poland",
  DE: "Germany",
  GB: "United Kingdom",
  US: "United States",
  IT: "Italy",
  HU: "Hungary",
  CN: "China",
  KR: "South Korea"
};

function countryName(code: string): string {
  return COUNTRY_NAMES[code] ?? code;
}

export function TargetAnalyzer({
  initialUniversity = "",
  initialLevel = "bachelor"
}: {
  initialUniversity?: string;
  initialLevel?: "bachelor" | "master";
}) {
  const [universityInput, setUniversityInput] = useState(initialUniversity);
  const [catalog, setCatalog] = useState<TargetCatalogItem[]>([]);
  const [level, setLevel] = useState<"bachelor" | "master">(initialLevel);
  const [qualification, setQualification] = useState<RouteQualification>(
    initialLevel === "master" ? "bachelor_degree" : "attestat"
  );
  const [gpa, setGpa] = useState("");
  const [gpaScale, setGpaScale] = useState<GradeScaleKey>("5.0");
  const [ielts, setIelts] = useState("");
  const [toefl, setToefl] = useState("");
  const [dimScore, setDimScore] = useState("");
  const [sat, setSat] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TargetGapResponse | null>(null);
  const [isPending, startTransition] = useTransition();

  // Load catalog for autocompletion
  useEffect(() => {
    let active = true;
    fetchTargetCatalog({ level })
      .then((items) => {
        if (active) setCatalog(items);
      })
      .catch(() => {
        // Handled silently; gap assessment handles errors explicitly
      });
    return () => {
      active = false;
    };
  }, [level]);

  // Adjust default qualification when level changes
  useEffect(() => {
    if (level === "master" && qualification === "attestat") {
      setQualification("bachelor_degree");
      setGpaScale("100");
    } else if (level === "bachelor" && qualification === "bachelor_degree") {
      setQualification("attestat");
      setGpaScale("5.0");
    }
  }, [level, qualification]);

  // Auto-run evaluation if initialUniversity is provided
  useEffect(() => {
    if (initialUniversity) {
      handleAnalyze(initialUniversity);
    }
  }, [initialUniversity]);

  async function handleAnalyze(targetName?: string) {
    const uniToAnalyze = (targetName ?? universityInput).trim();
    if (!uniToAnalyze) return;

    setLoading(true);
    setError(null);

    const payload: TargetGapPayload = {
      university_name: uniToAnalyze,
      level,
      qualification_held: qualification,
      gpa: gpa ? parseFloat(gpa) : undefined,
      gpa_scale: gpa ? gpaScale : undefined,
      ielts: ielts ? parseFloat(ielts) : undefined,
      toefl: toefl ? parseInt(toefl, 10) : undefined,
      dim_score: dimScore ? parseFloat(dimScore) : undefined,
      sat: sat ? parseInt(sat, 10) : undefined
    };

    try {
      const response = await assessTargetGap(payload);
      startTransition(() => {
        setResult(response);
      });
    } catch (err) {
      const parsed = getUserFacingError(err, "Target Gap Analysis");
      setError(parsed.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSelectUniversity(name: string) {
    setUniversityInput(name);
    handleAnalyze(name);
  }

  const catalogOptions = Array.from(
    new Set(catalog.map((item) => item.university_name))
  ).sort();

  return (
    <div className="space-y-8" data-testid="target-analyzer" aria-label="Target roadmap analysis">
      {/* Header & Description */}
      <section className="rounded-3xl border border-white/10 bg-[#13152c]/85 p-6 sm:p-8 backdrop-blur-2xl shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-br from-purple-500/20 to-orange-500/20 text-orange-400 shadow-inner">
            <Building2 size={22} />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-sans font-bold tracking-tight text-white">
              Target University Analyzer
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Objective gap analysis against specific institutional requirements.
              No arbitrary composite scores or speculative admission forecasts.
            </p>
          </div>
        </div>

        {/* Input Controls */}
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {/* Target Institution */}
          <div className="space-y-4">
            <div>
              <label
                htmlFor="target-university-input"
                className="block text-sm font-semibold text-slate-200"
              >
                Target University
              </label>
              <div className="relative mt-2">
                <input
                  id="target-university-input"
                  type="text"
                  list="target-catalog-list"
                  placeholder="e.g. Technical University of Munich, Oxford, METU"
                  value={universityInput}
                  onChange={(e) => setUniversityInput(e.target.value)}
                  className="field pr-10"
                />
                <Search
                  size={16}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <datalist id="target-catalog-list">
                  {catalogOptions.map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>
              </div>
              <p className="mt-1 text-xs text-slate-400">
                Choose from our curated catalogue or type any target institution.
              </p>
            </div>

            {/* Curated Quick Picks */}
            {catalogOptions.length > 0 && (
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Curated Catalog Quick Picks:
                </span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {catalogOptions.slice(0, 5).map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => handleSelectUniversity(name)}
                      className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                        universityInput === name
                          ? "bg-gradient-to-r from-orange-500 to-purple-600 text-white font-semibold shadow-md shadow-orange-500/20"
                          : "border border-white/10 bg-white/[0.04] text-slate-300 hover:border-white/20 hover:text-white"
                      }`}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Student Profile Input for Target Evaluation */}
          <div className="space-y-4 rounded-2xl border border-white/[0.08] p-5 bg-[#101226]/70 backdrop-blur-md">
            <h2 className="text-sm font-semibold text-white flex items-center gap-1.5">
              <GraduationCap size={16} className="text-orange-400" />
              Academic Credentials
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  Degree Level
                </label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value as "bachelor" | "master")}
                  className="field mt-1 text-xs"
                >
                  <option value="bachelor" className="bg-[#13152c] text-white">Bachelor</option>
                  <option value="master" className="bg-[#13152c] text-white">Master</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  Qualification Held
                </label>
                <select
                  value={qualification}
                  onChange={(e) =>
                    setQualification(e.target.value as RouteQualification)
                  }
                  className="field mt-1 text-xs"
                >
                  <option value="attestat" className="bg-[#13152c] text-white">Attestat (11-year)</option>
                  <option value="bachelor_degree" className="bg-[#13152c] text-white">Bachelor Degree</option>
                  <option value="ib_diploma" className="bg-[#13152c] text-white">IB Diploma</option>
                  <option value="a_levels" className="bg-[#13152c] text-white">A-Levels</option>
                </select>
              </div>
            </div>

            {/* GPA & Scale */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  Grade / GPA
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 4.8 or 85"
                  value={gpa}
                  onChange={(e) => setGpa(e.target.value)}
                  className="field mt-1 text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  Grade Scale
                </label>
                <select
                  value={gpaScale}
                  onChange={(e) => setGpaScale(e.target.value as GradeScaleKey)}
                  className="field mt-1 text-xs"
                >
                  {GRADE_SCALES.map((s) => (
                    <option key={s.value} value={s.value} className="bg-[#13152c] text-white">
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Standardized Tests */}
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  IELTS
                </label>
                <input
                  type="number"
                  step="0.5"
                  placeholder="7.0"
                  value={ielts}
                  onChange={(e) => setIelts(e.target.value)}
                  className="field mt-1 text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  TOEFL iBT
                </label>
                <input
                  type="number"
                  placeholder="95"
                  value={toefl}
                  onChange={(e) => setToefl(e.target.value)}
                  className="field mt-1 text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400">
                  DİM Score
                </label>
                <input
                  type="number"
                  placeholder="550"
                  value={dimScore}
                  onChange={(e) => setDimScore(e.target.value)}
                  className="field mt-1 text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Action button */}
        <div className="mt-7 flex justify-end">
          <button
            type="button"
            onClick={() => handleAnalyze()}
            disabled={loading || !universityInput.trim()}
            className="button-primary flex items-center gap-2 px-7 shadow-[0_0_25px_rgba(255,107,0,0.35)] min-h-12 text-sm"
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Assessing Requirements…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Analyze Target Gap
              </>
            )}
          </button>
        </div>
      </section>

      {/* Error state */}
      {error && (
        <div className="notice-error">
          <p className="font-semibold">Unable to assess target</p>
          <p className="mt-1 text-sm">{error}</p>
        </div>
      )}

      {/* Results panel */}
      {result && (
        <div className="space-y-6" data-testid="target-results">
          {/* Honest Uncurated Fallback State Banner (D2) */}
          {!result.found && (
            <div className="rounded-3xl border border-amber-500/30 bg-amber-500/[0.08] p-6 backdrop-blur-xl shadow-2xl">
              <div className="flex items-start gap-3.5">
                <HelpCircle className="h-6 w-6 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-sans text-lg font-bold text-amber-200">
                    Catalogue Gap (Our Data, Not an Admission Rejection)
                  </h3>
                  <p className="mt-1.5 text-sm text-slate-300 leading-6">
                    Requirements for <span className="font-semibold text-white">{result.university_name}</span> have not been collected or verified in the AUSA catalogue yet. This is a limitation of our current dataset, not an indication that the institution will reject your application.
                  </p>
                  <p className="mt-3 text-xs text-slate-400 leading-5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                    <strong className="text-slate-300">Speculative study plans excluded:</strong> AUSA does not invent speculative score targets or preparation schedules without empirical admission outcome models. Please check with the university&apos;s admissions office directly for official qualification equivalence.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Section 1: Route Gap Statement */}
          <section className="rounded-3xl border border-white/[0.08] bg-[#13152c]/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl" aria-labelledby="gap-statement-heading">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase tracking-widest text-slate-400">
                    {countryName(result.country_code)} · {result.level === "master" ? "Master's" : "Bachelor's"}
                  </span>
                </div>
                <h2 id="gap-statement-heading" className="text-2xl sm:text-3xl font-sans font-bold text-white mt-1">
                  {result.university_name}
                </h2>
                <p className="text-sm font-medium text-slate-400 mt-0.5">
                  {result.program_name}
                </p>
              </div>

              {/* Status Tag */}
              <div>
                {result.route_status === "OPEN" && (
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                    ✓ Route Open Directly
                  </span>
                )}
                {result.route_status === "UNLOCKABLE" && (
                  <span className="rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-wider text-orange-400">
                    ⚡ Route Unlockable via Bridge
                  </span>
                )}
                {result.route_status === "BLOCKED" && (
                  <span className="rounded-full border border-rose-500/30 bg-rose-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-wider text-rose-400">
                    ✕ Route Blocked
                  </span>
                )}
                {result.route_status === "UNKNOWN" && (
                  <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-wider text-purple-300">
                    ? Status Unverified
                  </span>
                )}
              </div>
            </div>

            {/* Gap Statement Callout */}
            <div
              className={`mt-6 rounded-2xl border p-5 backdrop-blur-md ${
                result.route_status === "OPEN"
                  ? "border-emerald-500/30 bg-emerald-500/[0.08] text-emerald-200"
                  : result.route_status === "UNLOCKABLE"
                    ? "border-orange-500/30 bg-orange-500/[0.08] text-orange-200"
                    : "border-purple-500/30 bg-purple-500/[0.08] text-purple-200"
              }`}
            >
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                1. Objective Gap Statement
              </h3>
              <p className="mt-2 text-sm leading-6">
                {result.route_gap_statement}
              </p>
            </div>

            {/* Unlock Steps & Requirements (if UNLOCKABLE or unlock_steps present) */}
            {result.unlock_steps && result.unlock_steps.length > 0 && (
              <div className="mt-6 border-t border-white/[0.08] pt-5">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Clock size={16} className="text-orange-400" />
                  What It Takes to Bridge the Gap:
                </h4>
                <ul className="mt-2 space-y-1.5 pl-5 list-disc text-sm text-slate-300">
                  {result.unlock_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>

                <dl className="mt-4 grid grid-cols-2 gap-4 text-xs bg-[#101226]/60 p-4 rounded-2xl border border-white/[0.08]">
                  <div>
                    <dt className="text-slate-400">Estimated Prep Duration:</dt>
                    <dd className="font-semibold text-white mt-0.5">
                      {result.unlock_time_months > 0
                        ? `${result.unlock_time_months} months`
                        : "Direct / immediate"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Estimated Pathway Cost:</dt>
                    <dd className="font-semibold text-white mt-0.5">
                      {result.unlock_cost_azn_low === 0 && result.unlock_cost_azn_high === 0
                        ? "Minimal / zero direct route fee"
                        : `${result.unlock_cost_azn_low.toLocaleString("en-US")} – ${result.unlock_cost_azn_high.toLocaleString("en-US")} AZN`}
                    </dd>
                  </div>
                </dl>
              </div>
            )}

            {/* Provenance & Last Checked footer */}
            <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-white/[0.08] pt-4 text-xs text-slate-400">
              {result.source_url && (
                <a
                  href={result.source_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-link inline-flex items-center gap-1 font-medium"
                >
                  Official Admission Requirements Page
                  <ExternalLink size={12} />
                </a>
              )}
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${
                  result.provenance === "human-verified"
                    ? "border border-emerald-500/30 bg-emerald-500/10 font-medium text-emerald-400"
                    : "border border-purple-500/30 bg-purple-500/10 font-normal text-purple-300"
                }`}
              >
                {result.provenance === "human-verified"
                  ? "✓ Checked by a person"
                  : "Read from official portal, not yet human-verified"}
              </span>
              {result.last_checked && (
                <span className="font-mono text-slate-500">Last verified: {result.last_checked.slice(0, 10)}</span>
              )}
            </div>
          </section>

          {/* Section 2: Scale-Aware Requirement Checklist */}
          <section className="rounded-3xl border border-white/[0.08] bg-[#13152c]/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl" aria-labelledby="requirement-checklist-heading">
            <div className="flex items-center justify-between">
              <div>
                <h3 id="requirement-checklist-heading" className="text-xl font-sans font-bold text-white">
                  2. Requirement Checklist
                </h3>
                <p className="mt-1 text-sm text-slate-400">
                  Multi-scale check comparing your academic profile and credentials against stated entry criteria.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {result.checklist.filter((c) => c.status === "MET").length} of {result.checklist.length} met
              </span>
            </div>

            <div className="mt-6 space-y-3">
              {result.checklist.map((item, idx) => {
                const isMet = item.status === "MET";
                const isGap = item.status === "GAP";
                const isUnknown = item.status === "UNKNOWN";

                return (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border border-white/[0.08] bg-[#101226]/60 backdrop-blur-md transition hover:border-white/20"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {isMet && <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />}
                        {isGap && <XCircle size={18} className="text-amber-400 shrink-0" />}
                        {isUnknown && <HelpCircle size={18} className="text-purple-400 shrink-0" />}
                        <h4 className="font-semibold text-sm text-white">{item.name}</h4>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        <span className="font-medium text-slate-200">Published Requirement: </span>
                        {item.requirement}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        <span className="font-medium text-slate-200">Your Profile: </span>
                        {item.student_value ?? "Not provided / Unstated"}
                      </p>
                      <p className="mt-1.5 text-xs text-slate-400 leading-5 border-l-2 border-white/10 pl-2.5">
                        {item.explanation}
                      </p>
                    </div>

                    <div className="sm:self-center shrink-0">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
                          isMet
                            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                            : isGap
                              ? "border-orange-500/30 bg-orange-500/10 text-orange-400"
                              : "border-purple-500/30 bg-purple-500/10 text-purple-300"
                        }`}
                      >
                        {isMet ? "✓ Met" : isGap ? "⚠ Gap" : "? Unknown"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <p className="mt-4 text-xs text-slate-500 leading-5 border-l-2 border-white/10 pl-3">
              Scale-awareness note: Grade comparisons across different grading systems (Attestat 5.0, Higher Ed 100, US 4.0, German 1.0-5.0) are indicative screening metrics. Universities conduct their own official conversions through bodies like uni-assist or internal credentials evaluators.
            </p>
          </section>

          {/* Section 3: Process Milestones & Deadlines */}
          <section className="rounded-3xl border border-white/[0.08] bg-[#13152c]/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl" aria-labelledby="process-milestones-heading">
            <h3 id="process-milestones-heading" className="text-xl font-sans font-bold text-white">
              3. Process Milestones &amp; Deadlines
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              Step-by-step operational timeline and verified application parameters for {result.university_name}.
            </p>

            {/* Key Application Parameters Grid */}
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/60 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Calendar size={14} className="text-orange-400" />
                  Application Deadline
                </span>
                <p className="mt-2 text-base font-bold text-white">
                  {result.application_deadline || "Not stated in catalogue"}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {result.application_deadline
                    ? "Check official portal for intake exceptions"
                    : "Confirm with admissions office"}
                </p>
              </div>

              <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/60 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <ExternalLink size={14} className="text-orange-400" />
                  Application Portal
                </span>
                <p className="mt-2 text-base font-bold text-white truncate">
                  {result.application_portal || "Direct institution portal"}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">Official submission gateway</p>
              </div>

              <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/60 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Building2 size={14} className="text-orange-400" />
                  Application Fee
                </span>
                <p className="mt-2 text-base font-bold text-white">
                  {result.application_fee !== null && result.application_fee !== undefined
                    ? `${result.application_fee} ${result.currency ?? ""}`.trim()
                    : "Not recorded (verify)"}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">Excludes visa &amp; courier fees</p>
              </div>

              <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/60 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Clock size={14} className="text-orange-400" />
                  Lead Time Needed
                </span>
                <p className="mt-2 text-base font-bold text-white">
                  {result.unlock_time_months > 0
                    ? `${result.unlock_time_months} months prep`
                    : "Direct application ready"}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">Pathway / preparation buffer</p>
              </div>
            </div>

            {/* Documents Required */}
            {result.documents_required && (
              <div className="mt-6 rounded-2xl border border-white/[0.08] bg-[#101226]/50 p-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Required Application Documents:
                </h4>
                <p className="mt-1.5 text-sm text-slate-200 leading-6">
                  {result.documents_required}
                </p>
              </div>
            )}

            {/* Step-by-Step Milestones Checklist */}
            <div className="mt-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Mandatory Execution Milestones:
              </h4>
              <ol className="mt-3 space-y-2.5 text-sm text-slate-300 pl-5 list-decimal">
                <li className="leading-6">
                  <span className="font-semibold text-white">Verify Intake &amp; Requirements:</span> Review the institution&apos;s published admission guidelines for your intended academic year and confirm that subject-specific prerequisites are met.
                </li>
                <li className="leading-6">
                  <span className="font-semibold text-white">Credential Evaluation:</span> Arrange certified translations and, if applying to institutions in Germany or the UK, initiate preliminary documentation clearance (e.g. uni-assist VPD or NARIC statement) at least 6 weeks before deadline.
                </li>
                <li className="leading-6">
                  <span className="font-semibold text-white">Standardized Examination:</span> Ensure all requisite language certificates (IELTS/TOEFL) and standardized tests (SAT, TR-YÖS, TestAS) are sat with official score reporting sent directly to the institution code.
                </li>
                <li className="leading-6">
                  <span className="font-semibold text-white">Portal Submission:</span> Submit application dossiers via {result.application_portal || "the institutional portal"} prior to {result.application_deadline || "the stated deadline"}.
                </li>
              </ol>
            </div>
          </section>

          {/* Section 4: Viable Alternatives Recommender */}
          <section className="rounded-3xl border border-white/[0.08] bg-[#13152c]/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl" aria-labelledby="alternatives-heading">
            <div className="flex items-center justify-between">
              <div>
                <h3 id="alternatives-heading" className="text-xl font-sans font-bold text-white">
                  4. Viable Alternatives Closing the Gap
                </h3>
                <p className="mt-1 text-sm text-slate-400">
                  Institutions offering comparable programs where your existing qualifications either open directly or require fewer bridge steps.
                </p>
              </div>
              <Sparkles size={20} className="text-orange-400 shrink-0" />
            </div>

            {result.alternatives && result.alternatives.length > 0 ? (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {result.alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between p-5 rounded-2xl border border-white/[0.08] bg-[#101226]/60 backdrop-blur-md transition hover:border-purple-500/30"
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        {countryName(alt.country_code)}
                      </span>
                      <h4 className="mt-1 text-base font-sans font-bold text-white">
                        {alt.university_name}
                      </h4>
                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        {alt.reason}
                      </p>
                    </div>
                    <div className="mt-4 pt-3 border-t border-white/[0.06] flex justify-end">
                      <button
                        type="button"
                        onClick={() => handleSelectUniversity(alt.university_name)}
                        className="button-secondary text-xs py-1.5 px-3.5"
                      >
                        Target This Alternative
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-6 p-5 rounded-2xl border border-white/[0.08] bg-[#101226]/40 text-sm text-slate-400">
                <p>
                  No direct alternatives are recorded in our current catalogue for this specific target.
                  Use the Discovery Route Planner to view all open and unlockable pathways matching your profile.
                </p>
                <div className="mt-3">
                  <a href="/plan" className="text-link text-xs font-semibold inline-flex items-center gap-1">
                    Open Discovery Route Planner →
                  </a>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
