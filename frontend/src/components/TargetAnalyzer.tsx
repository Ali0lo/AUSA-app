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
  { value: "az_attestat_5", label: "Azerbaijan Attestat (3.0 – 5.0)" },
  { value: "az_he_100", label: "Azerbaijani Higher Ed (0 – 100)" },
  { value: "us_gpa_4", label: "US / International GPA (0.0 – 4.0)" },
  { value: "de_gpa_5", label: "German Scale (1.0 best – 5.0 fail)" },
  { value: "ru_attestat_5", label: "Russian Attestat (3.0 – 5.0)" }
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
  const [gpaScale, setGpaScale] = useState<GradeScaleKey>("az_attestat_5");
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
      setGpaScale("az_he_100");
    } else if (level === "bachelor" && qualification === "bachelor_degree") {
      setQualification("attestat");
      setGpaScale("az_attestat_5");
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
    <div className="space-y-8" aria-label="Target University Analyzer">
      {/* Header & Description */}
      <section className="panel p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <Building2 size={22} />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold tracking-tight text-ink">
              Target University Analyzer
            </h1>
            <p className="mt-1 text-sm text-muted">
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
                className="block text-sm font-semibold text-ink"
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted"
                />
                <datalist id="target-catalog-list">
                  {catalogOptions.map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>
              </div>
              <p className="mt-1 text-xs text-muted">
                Choose from our curated catalogue or type any target institution.
              </p>
            </div>

            {/* Curated Quick Picks */}
            {catalogOptions.length > 0 && (
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Curated Catalog Quick Picks:
                </span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {catalogOptions.slice(0, 5).map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => handleSelectUniversity(name)}
                      className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                        universityInput === name
                          ? "bg-accent text-paper"
                          : "bg-quiet hover:bg-line text-ink"
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
          <div className="space-y-4 rounded-lg border border-quiet p-4 bg-paper/50">
            <h2 className="text-sm font-semibold text-ink flex items-center gap-1.5">
              <GraduationCap size={16} className="text-accent" />
              Academic Credentials
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-muted">
                  Degree Level
                </label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value as "bachelor" | "master")}
                  className="field mt-1 text-xs"
                >
                  <option value="bachelor">Bachelor</option>
                  <option value="master">Master</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted">
                  Qualification Held
                </label>
                <select
                  value={qualification}
                  onChange={(e) =>
                    setQualification(e.target.value as RouteQualification)
                  }
                  className="field mt-1 text-xs"
                >
                  <option value="attestat">Attestat (11-year)</option>
                  <option value="bachelor_degree">Bachelor Degree</option>
                  <option value="ib_diploma">IB Diploma</option>
                  <option value="a_levels">A-Levels</option>
                </select>
              </div>
            </div>

            {/* GPA & Scale */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-muted">
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
                <label className="block text-xs font-semibold text-muted">
                  Grade Scale
                </label>
                <select
                  value={gpaScale}
                  onChange={(e) => setGpaScale(e.target.value as GradeScaleKey)}
                  className="field mt-1 text-xs"
                >
                  {GRADE_SCALES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Standardized Tests */}
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-semibold text-muted">
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
                <label className="block text-xs font-semibold text-muted">
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
                <label className="block text-xs font-semibold text-muted">
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
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={() => handleAnalyze()}
            disabled={loading || !universityInput.trim()}
            className="button-primary flex items-center gap-2"
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
          {/* Section 1: Route Gap Statement */}
          <section className="panel p-6 sm:p-8" aria-labelledby="gap-statement-heading">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase tracking-widest text-muted">
                    {countryName(result.country_code)} · {result.level === "master" ? "Master's" : "Bachelor's"}
                  </span>
                </div>
                <h2 id="gap-statement-heading" className="text-2xl font-serif font-bold text-ink mt-1">
                  {result.university_name}
                </h2>
                <p className="text-sm font-medium text-muted mt-0.5">
                  {result.program_name}
                </p>
              </div>

              {/* Status Tag */}
              <div>
                {result.route_status === "OPEN" && (
                  <span className="status-tag status-available text-xs">
                    ✓ Route Open Directly
                  </span>
                )}
                {result.route_status === "UNLOCKABLE" && (
                  <span className="status-tag status-experimental text-xs">
                    ⚡ Route Unlockable via Bridge
                  </span>
                )}
                {result.route_status === "BLOCKED" && (
                  <span className="status-tag status-offline text-xs">
                    ✕ Route Blocked
                  </span>
                )}
                {result.route_status === "UNKNOWN" && (
                  <span className="status-tag status-offline text-xs">
                    ? Status Unverified
                  </span>
                )}
              </div>
            </div>

            {/* Gap Statement Callout */}
            <div
              className={`mt-6 rounded-lg border p-4 ${
                result.route_status === "OPEN"
                  ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200"
                  : result.route_status === "UNLOCKABLE"
                    ? "border-amber-200 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200"
                    : "border-quiet bg-paper/60 text-ink"
              }`}
            >
              <h3 className="text-xs font-bold uppercase tracking-wider">
                1. Objective Gap Statement
              </h3>
              <p className="mt-2 text-sm leading-6">
                {result.route_gap_statement}
              </p>
            </div>

            {/* Unlock Steps & Requirements (if UNLOCKABLE or unlock_steps present) */}
            {result.unlock_steps && result.unlock_steps.length > 0 && (
              <div className="mt-6 border-t border-quiet pt-4">
                <h4 className="text-sm font-semibold text-ink flex items-center gap-2">
                  <Clock size={16} className="text-accent" />
                  What It Takes to Bridge the Gap:
                </h4>
                <ul className="mt-2 space-y-1.5 pl-5 list-disc text-sm text-ink">
                  {result.unlock_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>

                <dl className="mt-4 grid grid-cols-2 gap-4 text-xs bg-paper/40 p-3 rounded border border-quiet">
                  <div>
                    <dt className="text-muted">Estimated Prep Duration:</dt>
                    <dd className="font-semibold text-ink">
                      {result.unlock_time_months > 0
                        ? `${result.unlock_time_months} months`
                        : "Direct / immediate"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted">Estimated Pathway Cost:</dt>
                    <dd className="font-semibold text-ink">
                      {result.unlock_cost_azn_low === 0 && result.unlock_cost_azn_high === 0
                        ? "Minimal / zero direct route fee"
                        : `${result.unlock_cost_azn_low.toLocaleString("en-US")} – ${result.unlock_cost_azn_high.toLocaleString("en-US")} AZN`}
                    </dd>
                  </div>
                </dl>
              </div>
            )}

            {/* Provenance & Last Checked footer */}
            <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-quiet pt-4 text-xs text-muted">
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
                className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs ${
                  result.provenance === "human-verified"
                    ? "border border-emerald-300 bg-emerald-50 font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : "border border-amber-300 bg-amber-50 font-normal text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300"
                }`}
              >
                {result.provenance === "human-verified"
                  ? "✓ Checked by a person"
                  : "Read from official portal, not yet human-verified"}
              </span>
              {result.last_checked && (
                <span className="font-mono">Last verified: {result.last_checked.slice(0, 10)}</span>
              )}
            </div>
          </section>

          {/* Section 2: Scale-Aware Requirement Checklist */}
          <section className="panel p-6 sm:p-8" aria-labelledby="requirement-checklist-heading">
            <div className="flex items-center justify-between">
              <div>
                <h3 id="requirement-checklist-heading" className="text-xl font-serif font-bold text-ink">
                  2. Requirement Checklist
                </h3>
                <p className="mt-1 text-sm text-muted">
                  Multi-scale check comparing your academic profile and credentials against stated entry criteria.
                </p>
              </div>
              <span className="text-xs font-mono text-muted">
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
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border border-quiet bg-paper/40 transition hover:bg-paper/70"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {isMet && <CheckCircle2 size={18} className="text-success shrink-0" />}
                        {isGap && <XCircle size={18} className="text-warning shrink-0" />}
                        {isUnknown && <HelpCircle size={18} className="text-muted shrink-0" />}
                        <h4 className="font-semibold text-sm text-ink">{item.name}</h4>
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        <span className="font-medium text-ink">Published Requirement: </span>
                        {item.requirement}
                      </p>
                      <p className="mt-0.5 text-xs text-muted">
                        <span className="font-medium text-ink">Your Profile: </span>
                        {item.student_value ?? "Not provided / Unstated"}
                      </p>
                      <p className="mt-1.5 text-xs text-muted leading-5 border-l-2 border-quiet pl-2.5">
                        {item.explanation}
                      </p>
                    </div>

                    <div className="sm:self-center shrink-0">
                      <span
                        className={`status-tag text-xs font-semibold ${
                          isMet
                            ? "status-available"
                            : isGap
                              ? "status-experimental"
                              : "status-offline"
                        }`}
                      >
                        {isMet ? "✓ Met" : isGap ? "⚠ Gap" : "? Unknown"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <p className="mt-4 text-xs text-muted leading-5 border-l-2 border-quiet pl-3">
              Scale-awareness note: Grade comparisons across different grading systems (Attestat 5.0, Higher Ed 100, US 4.0, German 1.0-5.0) are indicative screening metrics. Universities conduct their own official conversions through bodies like uni-assist or internal credentials evaluators.
            </p>
          </section>

          {/* Section 3: Process Milestones & Deadlines */}
          <section className="panel p-6 sm:p-8" aria-labelledby="process-milestones-heading">
            <h3 id="process-milestones-heading" className="text-xl font-serif font-bold text-ink">
              3. Process Milestones &amp; Deadlines
            </h3>
            <p className="mt-1 text-sm text-muted">
              Step-by-step operational timeline and verified application parameters for {result.university_name}.
            </p>

            {/* Key Application Parameters Grid */}
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border border-quiet bg-paper/50 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
                  <Calendar size={14} className="text-accent" />
                  Application Deadline
                </span>
                <p className="mt-2 text-base font-bold text-ink">
                  {result.application_deadline || "Not stated in catalogue"}
                </p>
                <p className="mt-0.5 text-xs text-muted">
                  {result.application_deadline
                    ? "Check official portal for intake exceptions"
                    : "Confirm with admissions office"}
                </p>
              </div>

              <div className="rounded-lg border border-quiet bg-paper/50 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
                  <ExternalLink size={14} className="text-accent" />
                  Application Portal
                </span>
                <p className="mt-2 text-base font-bold text-ink truncate">
                  {result.application_portal || "Direct institution portal"}
                </p>
                <p className="mt-0.5 text-xs text-muted">Official submission gateway</p>
              </div>

              <div className="rounded-lg border border-quiet bg-paper/50 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
                  <Building2 size={14} className="text-accent" />
                  Application Fee
                </span>
                <p className="mt-2 text-base font-bold text-ink">
                  {result.application_fee !== null && result.application_fee !== undefined
                    ? `${result.application_fee} ${result.currency ?? ""}`.trim()
                    : "Not recorded (verify)"}
                </p>
                <p className="mt-0.5 text-xs text-muted">Excludes visa &amp; courier fees</p>
              </div>

              <div className="rounded-lg border border-quiet bg-paper/50 p-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
                  <Clock size={14} className="text-accent" />
                  Lead Time Needed
                </span>
                <p className="mt-2 text-base font-bold text-ink">
                  {result.unlock_time_months > 0
                    ? `${result.unlock_time_months} months prep`
                    : "Direct application ready"}
                </p>
                <p className="mt-0.5 text-xs text-muted">Pathway / preparation buffer</p>
              </div>
            </div>

            {/* Documents Required */}
            {result.documents_required && (
              <div className="mt-6 rounded-lg border border-quiet bg-paper/30 p-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted">
                  Required Application Documents:
                </h4>
                <p className="mt-1.5 text-sm text-ink leading-6">
                  {result.documents_required}
                </p>
              </div>
            )}

            {/* Step-by-Step Milestones Checklist */}
            <div className="mt-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted">
                Mandatory Execution Milestones:
              </h4>
              <ol className="mt-3 space-y-2.5 text-sm text-ink pl-5 list-decimal">
                <li className="leading-6">
                  <span className="font-semibold">Verify Intake &amp; Requirements:</span> Review the institution&apos;s published admission guidelines for your intended academic year and confirm that subject-specific prerequisites are met.
                </li>
                <li className="leading-6">
                  <span className="font-semibold">Credential Evaluation:</span> Arrange certified translations and, if applying to institutions in Germany or the UK, initiate preliminary documentation clearance (e.g. uni-assist VPD or NARIC statement) at least 6 weeks before deadline.
                </li>
                <li className="leading-6">
                  <span className="font-semibold">Standardized Examination:</span> Ensure all requisite language certificates (IELTS/TOEFL) and standardized tests (SAT, TR-YÖS, TestAS) are sat with official score reporting sent directly to the institution code.
                </li>
                <li className="leading-6">
                  <span className="font-semibold">Portal Submission:</span> Submit application dossiers via {result.application_portal || "the institutional portal"} prior to {result.application_deadline || "the stated deadline"}.
                </li>
              </ol>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
