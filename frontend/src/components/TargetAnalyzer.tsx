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

      {/* Results placeholder */}
      {result && (
        <div className="space-y-6" data-testid="target-results">
          {/* Detailed sections will be layered in Commits 12-16 */}
          <div className="panel p-6">
            <h2 className="text-xl font-serif font-bold">
              {result.university_name} — {result.program_name}
            </h2>
            <p className="text-sm text-muted mt-1">{result.route_gap_statement}</p>
          </div>
        </div>
      )}
    </div>
  );
}
