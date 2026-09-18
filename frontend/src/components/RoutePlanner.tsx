"use client";

import {
  ArrowRight,
  ExternalLink,
  Loader2,
  Compass,
  Crosshair,
  Sparkles
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { assessRoutes, getUserFacingError } from "@/lib/api";
import baselineFixture from "@/lib/baseline-routes.json";
import { CatalogueTarget } from "@/components/CatalogueTarget";
import type {
  AssessRoutesPayload,
  AssessRoutesResponse,
  GradeScaleKey,
  RoutePlan,
  RouteQualification,
  RouteUniversity,
  Scholarship
} from "@/types";

const QUALIFICATIONS: { value: RouteQualification; label: string }[] = [
  { value: "attestat", label: "Orta təhsil haqqında attestat (school certificate)" },
  { value: "one_year_university", label: "One completed year at an Azerbaijani university" },
  { value: "bachelor_degree", label: "A completed bachelor's degree" },
  { value: "foundation_year", label: "A completed international foundation year" },
  { value: "feststellungspruefung", label: "Feststellungsprüfung (completed Studienkolleg exam)" },
  { value: "a_level", label: "A Levels" },
  { value: "ib", label: "International Baccalaureate" }
];

const GRADE_SCALES: { value: GradeScaleKey; label: string }[] = [
  { value: "5.0", label: "out of 5 — the usual attestat scale" },
  { value: "100", label: "out of 100 — most Azerbaijani and Turkish universities" },
  { value: "4.0", label: "out of 4.0 — US-style GPA" },
  { value: "german", label: "German 1.0–4.0 — where 1.0 is best" }
];

const DESTINATION_OPTIONS: { code: string; label: string }[] = [
  { code: "TR", label: "Turkey (TR)" },
  { code: "DE", label: "Germany (DE)" },
  { code: "GB", label: "United Kingdom (GB)" },
  { code: "US", label: "United States (US)" },
  { code: "PL", label: "Poland (PL)" },
  { code: "CN", label: "China (CN)" }
];

const FIELD_OPTIONS: { value: string; label: string; dimGroup?: number }[] = [
  { value: "", label: "All fields / general" },
  { value: "engineering", label: "Engineering & Technology (DİM Group 1)", dimGroup: 1 },
  { value: "cs", label: "Computer Science & Information Technology (DİM Group 1)", dimGroup: 1 },
  { value: "business", label: "Economics, Finance & Business (DİM Group 2)", dimGroup: 2 },
  { value: "social", label: "Social Sciences & Law (DİM Group 3)", dimGroup: 3 },
  { value: "natural_sciences", label: "Natural Sciences & Medicine (DİM Group 4)", dimGroup: 4 }
];

const COUNTRY_NAMES: Record<string, string> = {
  AZ: "Azerbaijan",
  TR: "Turkey",
  DE: "Germany",
  GB: "United Kingdom",
  US: "United States",
  PL: "Poland",
  CN: "China"
};

function countryName(code: string): string {
  return COUNTRY_NAMES[code] ?? code;
}

function money(low: number, high: number): string {
  if (low === 0 && high === 0) return "no direct cost recorded";
  if (low === high) return `${low.toLocaleString("en-US")} AZN`;
  return `${low.toLocaleString("en-US")}–${high.toLocaleString("en-US")} AZN`;
}

function months(total: number): string {
  if (total === 0) return "no extra time";
  if (total === 12) return "1 extra year";
  return `${total} months`;
}

/** A blank number input is absent, never zero. */
function num(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function GradeLine({ university }: { university: RouteUniversity }) {
  const { grade_verdict: verdict, grade_exact: exact, grade_explanation: explanation } = university;
  if (verdict === "no_minimum_published") return null;

  const tone =
    verdict === "meets" ? "text-success" : verdict === "below" ? "text-warning" : "text-muted";
  const label =
    verdict === "meets"
      ? exact
        ? "Clears the stated minimum"
        : "Appears to clear the minimum"
      : verdict === "below"
        ? "Below the stated minimum"
        : verdict === "no_grade_given"
          ? "Grade not entered"
          : "Grades not comparable";

  return (
    <div className="mt-3 border-l-2 border-quiet pl-3">
      <p className={`text-sm font-semibold ${tone}`}>
        {label}
        {verdict === "meets" && !exact && (
          <span className="ml-2 font-normal text-muted">— rough comparison, not an official conversion</span>
        )}
      </p>
      <p className="mt-1 text-xs leading-5 text-muted">{explanation}</p>
    </div>
  );
}

function UniversityCard({
  university,
  onTarget
}: {
  university: RouteUniversity;
  onTarget?: (name: string) => void;
}) {
  const facts: [string, string][] = [];

  if (university.tuition_per_year != null) {
    facts.push([
      "Tuition per year",
      `${university.tuition_per_year.toLocaleString("en-US")} ${university.currency ?? ""}`.trim()
    ]);
  } else {
    facts.push(["Tuition per year", "Not recorded in the catalogue (unknown, not free)"]);
  }

  if (university.application_deadline) {
    facts.push(["Deadline", university.application_deadline]);
  } else {
    facts.push(["Deadline", "Not recorded in the catalogue"]);
  }

  if (university.language_test) {
    facts.push([
      "Language",
      university.language_minimum_score !== null
        ? `${university.language_test} ${university.language_minimum_score}`
        : `${university.language_test} — minimum not recorded`
    ]);
  } else {
    facts.push(["Language", "Not recorded in the catalogue (unknown, not 'none required')"]);
  }

  if (university.entrance_exam) {
    facts.push([
      "Entrance exam",
      university.entrance_exam_minimum !== null
        ? `${university.entrance_exam} ${university.entrance_exam_minimum}`
        : `${university.entrance_exam} — minimum not recorded`
    ]);
  } else {
    facts.push(["Entrance exam", "Not recorded; check the source"]);
  }

  if (university.gpa_minimum !== null) {
    facts.push([
      "Minimum grade",
      `${university.gpa_minimum}${university.gpa_scale ? ` out of ${university.gpa_scale}` : ""}`
    ]);
  }

  if (university.application_portal) {
    facts.push(["Apply via", university.application_portal]);
  } else {
    facts.push(["Apply via", "Not recorded in the catalogue"]);
  }

  return (
    <article className="rounded-2xl border border-white/[0.08] bg-[#101226]/75 p-5 mt-4 backdrop-blur-md transition-all hover:border-white/[0.15]">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h4 className="font-sans text-lg font-bold text-white">{university.university_name}</h4>
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-[0.12em] text-slate-400">
            {countryName(university.country_code)} · {university.intake_year} intake
          </span>
          {onTarget && (
            <button
              type="button"
              onClick={() => onTarget(university.university_name)}
              className="inline-flex items-center gap-1 rounded-full border border-orange-500/30 bg-orange-500/10 px-2.5 py-0.5 text-xs font-semibold text-orange-300 transition-colors hover:bg-orange-500/20 ml-2"
            >
              <Crosshair size={12} aria-hidden="true" />
              Target
            </button>
          )}
        </div>
      </div>
      <p className="mt-1 text-sm text-slate-300">{university.program_name}</p>

      {facts.length > 0 && (
        <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {facts.map(([term, value]) => (
            <div key={term} className="flex justify-between gap-3 border-b border-white/[0.06] pb-1.5 text-sm">
              <dt className="text-slate-400">{term}</dt>
              <dd className="text-right font-medium text-slate-200">{value}</dd>
            </div>
          ))}
        </dl>
      )}

      <GradeLine university={university} />
      {university.application_status && university.application_status !== "needs_review" && <p className="mt-3 font-semibold text-amber-400">{university.application_status.replace(/_/g, " ")}</p>}
      {university.checks?.length ? <ul className="mt-3 list-disc pl-5 text-sm text-slate-400">{university.checks.map((check) => <li key={check}>{check}</li>)}</ul> : null}
      {university.notes && <p className="mt-3 whitespace-pre-line text-sm text-slate-400">{university.notes}</p>}
      {university.living_cost_estimate_per_year != null && <p className="mt-2 text-sm text-slate-300">Annual living estimate: {university.living_cost_estimate_per_year.toLocaleString("en-US")} {university.currency}</p>}
      {university.application_fee != null && <p className="mt-2 text-sm text-slate-300">Application fee: {university.application_fee} {university.currency}</p>}
      {university.evidence?.length ? <details className="mt-3 text-sm text-slate-300"><summary className="cursor-pointer font-medium text-orange-400 hover:text-orange-300">Evidence and scope</summary><ul className="mt-2 space-y-2">{university.evidence.map((item, index) => <li key={index}><a className="text-link" href={/^https?:\/\//i.test(item.url) ? item.url : undefined} target="_blank" rel="noreferrer noopener">{item.fields.map((field) => field.replace(/_/g, " ")).join(", ")}</a>: {item.note} (Read {item.checked_at})</li>)}</ul></details> : null}

      {/* The unknowns, said out loud. */}
      {university.unknown_fields && university.unknown_fields.length > 0 && (
        <div className="mt-3 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs leading-5 text-slate-300">
          <span className="font-semibold text-amber-400">Not stated on institution website: </span>
          {university.unknown_fields.map((f) => f.replace(/_/g, " ")).join(", ")}
        </div>
      )}

      {university.not_stated && (
        <p className="mt-3 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs leading-5 text-slate-300">
          {university.not_stated}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
        <a
          className="text-link inline-flex items-center gap-1"
          href={university.source_url}
          target="_blank"
          rel="noreferrer noopener"
        >
          Source page
          <ExternalLink size={12} aria-hidden="true" />
        </a>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${
            university.provenance === "human-verified"
              ? "border border-emerald-500/30 bg-emerald-500/10 font-medium text-emerald-400"
              : "border border-purple-500/30 bg-purple-500/10 font-normal text-purple-300"
          }`}
        >
          {university.provenance === "human-verified"
            ? "✓ Checked by a person"
            : "Read from the source page, not yet checked by a person"}
        </span>
        {university.last_checked && (
          <span className="font-mono text-xs text-slate-500">Last checked: {university.last_checked.slice(0, 10)}</span>
        )}
      </div>
    </article>
  );
}

function PlanCard({
  plan,
  index,
  budget,
  onTargetUniversity
}: {
  plan: RoutePlan;
  index: number;
  budget?: number;
  onTargetUniversity?: (uniName: string) => void;
}) {
  const isOpen = plan.status === "open";
  const isDirect = plan.hops.length === 1;
  const isBridge = plan.hops.length > 1;

  return (
    <section className="rounded-3xl border border-white/[0.08] bg-[#13152c]/75 p-6 sm:p-8 backdrop-blur-xl shadow-2xl transition-all duration-300 hover:border-white/[0.15] mt-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Option {String(index + 1).padStart(2, "0")}</p>
          <h3 className="font-sans text-2xl sm:text-3xl font-bold text-white mt-2">
            {countryName(plan.destination_country)}
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {isDirect ? (
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">
              1-hop direct route
            </span>
          ) : (
            <span className="rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-orange-400">
              2-hop bridge ({plan.hops[0]?.mechanism || "pathway"})
            </span>
          )}
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
            isOpen
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
              : "border-purple-500/30 bg-purple-500/10 text-purple-300"
          }`}>
            {isOpen ? "Open now" : "Needs something first"}
          </span>
        </div>
      </div>

      <ol className="mt-6 divide-y divide-white/[0.08] border-y border-white/[0.08]">
        {plan.hops.map((hop, hopIndex) => {
          const isBridgeHop = isBridge && hopIndex === 0;
          const isFinalHop = isBridge && hopIndex === plan.hops.length - 1;
          return (
            <li key={hop.key} className="flex gap-4 py-4">
              <span className="font-sans text-xl font-extrabold bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
                {hopIndex + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-white">{hop.mechanism}</p>
                  {isBridgeHop && (
                    <span className="rounded-full border border-orange-500/30 bg-orange-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-orange-300">
                      Bridge Step
                    </span>
                  )}
                  {isFinalHop && (
                    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-300">
                      Target Degree
                    </span>
                  )}
                  {isDirect && (
                    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-300">
                      Direct Entry
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  {countryName(hop.country_code)} · {months(hop.time_cost_months)} ·{" "}
                  {money(hop.money_cost_azn_low, hop.money_cost_azn_high)}
                </p>
                {hop.proof_of_funds && (
                  <p className="mt-2 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs leading-5 text-slate-300">
                    <span className="font-semibold text-amber-300">
                      {hop.proof_of_funds.amount.toLocaleString()} {hop.proof_of_funds.currency}{" "}
                      {hop.proof_of_funds.period}, in the bank before the visa.
                    </span>{" "}
                    <span className="text-slate-400">{hop.proof_of_funds.mechanism}.</span>{" "}
                    <span className="text-slate-400">
                      This is separate from the cost above — the money stays yours.
                    </span>
                  </p>
                )}
                <p className="mt-1 text-xs leading-5 text-slate-500">{hop.citation}</p>
              </div>
            </li>
          );
        })}
      </ol>

      <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <div>
          <dt className="text-slate-400">Extra time</dt>
          <dd className="font-semibold text-white">{months(plan.total_months)}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Estimated route cost</dt>
          <dd className="font-semibold text-white">
            {money(plan.total_cost_azn_low, plan.total_cost_azn_high)}
          </dd>
        </div>
        <div>
          <dt className="text-slate-400">You would apply holding</dt>
          <dd className="font-semibold text-white">{plan.qualification_delivered.replace(/_/g, " ")}</dd>
        </div>
      </dl>

      {/* Tuition transparency notice (D1.5 / D3) */}
      {(
        <p className="mt-4 rounded-xl border border-white/[0.08] bg-white/[0.02] p-3 text-xs leading-5 text-slate-400">
          Route estimates are rough planning figures. Full cost to degree is unavailable: programme duration, tuition changes, living expenses and currency conversion have not all been assessed. Unknown tuition is not free.
        </p>
      )}

      {/* Budget headroom check */}
      {budget !== undefined && (
        <div className="mt-4 text-xs">
          {plan.total_cost_azn_high <= budget ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 font-semibold text-emerald-300">
              ✓ Route entry cost fits within your stated budget of {budget.toLocaleString("en-US")} AZN/year.
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3.5 py-1.5 font-semibold text-amber-300">
              ⚠ Route entry cost ({plan.total_cost_azn_low.toLocaleString("en-US")}–{plan.total_cost_azn_high.toLocaleString("en-US")} AZN) exceeds your stated budget of {budget.toLocaleString("en-US")} AZN/year. Scholarships or funding will be needed.
            </span>
          )}
        </div>
      )}

      {plan.missing.length > 0 && (
        <div className="mt-5 rounded-2xl border border-amber-500/20 bg-amber-500/[0.08] p-4 text-amber-200 backdrop-blur-md">
          <p className="font-semibold text-amber-300">Before this route opens:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs sm:text-sm">
            {plan.missing.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
          {plan.universities.length > 0
            ? `${plan.universities.length} ${plan.universities.length === 1 ? "university accepts" : "universities accept"} what this route gives you`
            : "Universities"}
        </p>

        {plan.universities.length > 0 ? (
          <div className="mt-1">
            {plan.universities.map((university) => (
              <UniversityCard
                key={`${university.university_name}-${university.program_name}`}
                university={university}
                onTarget={onTargetUniversity}
              />
            ))}
          </div>
        ) : (
          <div className="mt-2 text-sm leading-6 text-slate-400 rounded-2xl border border-white/[0.08] bg-[#101226]/50 p-4">
            {plan.universities_status === "no_requirements_collected_for_this_country_yet" && (
              <span className="block font-semibold text-xs uppercase tracking-wider text-purple-400 mb-1">
                Catalogue gap (our data)
              </span>
            )}
            {plan.universities_status === "no_curated_universities_accept_qualification" && (
              <span className="block font-semibold text-xs uppercase tracking-wider text-amber-400 mb-1">
                Finding about this country
              </span>
            )}
            <p>{plan.universities_explanation}</p>
          </div>
        )}
      </div>
    </section>
  );
}

const TIER_NAMES: Record<number, string> = {
  1: "Azerbaijani state",
  2: "Destination government",
  3: "University"
};

const SCHOLARSHIP_HEADLINE: Record<string, string> = {
  open: "You meet the published requirements",
  unlockable: "Not yet — here is what stands between you and it",
  blocked: "Closed to you"
};

function ScholarshipCard({ scholarship }: { scholarship: Scholarship }) {
  return (
    <article className="rounded-2xl border border-white/[0.08] bg-[#101226]/75 p-5 mt-4 backdrop-blur-md transition-all hover:border-white/[0.15]">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h4 className="font-sans text-lg font-bold text-white">{scholarship.name}</h4>
        <span className="text-xs uppercase tracking-[0.12em] text-slate-400">
          {TIER_NAMES[scholarship.tier] ?? "Funding"}
          {scholarship.country_code ? ` · ${countryName(scholarship.country_code)}` : ""}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-400">{scholarship.provider}</p>

      <p
        className={`mt-3 text-sm font-semibold ${
          scholarship.status === "open"
            ? "text-emerald-400"
            : scholarship.status === "blocked"
              ? "text-slate-400"
              : "text-amber-400"
        }`}
      >
        {SCHOLARSHIP_HEADLINE[scholarship.status] ?? scholarship.status}
      </p>

      <p className="mt-2 text-sm leading-6 text-slate-300">{scholarship.coverage}</p>

      {scholarship.gates_met.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-emerald-400">
          {scholarship.gates_met.map((gate) => <li key={gate}>✓ {gate}</li>)}
        </ul>
      )}
      {scholarship.gates_blocked.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm text-slate-400">
          {scholarship.gates_blocked.map((gate) => <li key={gate}>✕ {gate}</li>)}
        </ul>
      )}
      {scholarship.gates_missing.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm text-amber-400">
          {scholarship.gates_missing.map((gate) => <li key={gate}>· {gate}</li>)}
        </ul>
      )}

      {/* Rendered apart from the list above, and labelled */}
      {scholarship.gates_unknown.length > 0 && (
        <div className="mt-3 rounded-xl border border-purple-500/20 bg-purple-500/[0.05] p-3 text-xs leading-5 text-slate-300">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-purple-300">
            What we could not check
          </p>
          <ul className="mt-1 space-y-1 text-sm leading-6 text-slate-400">
            {scholarship.gates_unknown.map((gate) => <li key={gate}>{gate}</li>)}
          </ul>
        </div>
      )}

      {scholarship.window && (
        <p className="mt-3 text-xs leading-5 text-slate-400">
          <span className="font-semibold text-slate-300">When: </span>
          {scholarship.window}
        </p>
      )}
      {scholarship.obligation && (
        <p className="mt-2 text-xs leading-5 text-slate-400">
          <span className="font-semibold text-slate-300">What you commit to: </span>
          {scholarship.obligation}
        </p>
      )}

      <p className="mt-3 text-xs leading-5 text-slate-500">
        {scholarship.citation} · {scholarship.provenance}, not yet verified by a person.
      </p>
    </article>
  );
}

export function RoutePlanner() {
  const [mode, setMode] = useState<"discovery" | "target">("discovery");
  const [level, setLevel] = useState<"bachelor" | "master">("bachelor");
  const [qualification, setQualification] = useState<RouteQualification>("attestat");
  const [gpa, setGpa] = useState("");
  const [gpaScale, setGpaScale] = useState<GradeScaleKey>("5.0");
  const [ielts, setIelts] = useState("");
  const [toefl, setToefl] = useState("");
  const [dim, setDim] = useState("");
  const [dimGroup, setDimGroup] = useState("");
  const [sat, setSat] = useState("");
  const [trYos, setTrYos] = useState("");
  const [testAs, setTestAs] = useState("");
  const [csca, setCsca] = useState("");
  const [hsk, setHsk] = useState("");
  const [language, setLanguage] = useState("");
  const [budget, setBudget] = useState("");
  const [preferredDestinations, setPreferredDestinations] = useState<string[]>([]);
  const [fieldOfStudy, setFieldOfStudy] = useState("");

  // Funding inputs
  const [age, setAge] = useState("");
  const [workHours, setWorkHours] = useState("");
  const [employer, setEmployer] = useState("");

  const [result, setResult] = useState<AssessRoutesResponse | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);
  const [pending, setPending] = useState(false);

  // Target university selection
  const [targetUniversity, setTargetUniversity] = useState("Bogazici University");

  // Determine active dataset to display:
  // If user submitted or loaded from API, use result.
  // Otherwise, use baselineFixture so the page is never empty before input.
  const activeResult: AssessRoutesResponse | null = useMemo(() => {
    if (error) return null;
    if (result) return result;
    return baselineFixture as unknown as AssessRoutesResponse;
  }, [result, error]);

  // Destination filtering & ranking (D1.4: Destination ranks, never excludes)
  const { mainPlans, outsidePlans } = useMemo(() => {
    if (!activeResult) return { mainPlans: [], outsidePlans: [] };
    const sortPlans = (plans: RoutePlan[]) =>
      [...plans].sort((a, b) => {
        if (a.status === "open" && b.status !== "open") return -1;
        if (a.status !== "open" && b.status === "open") return 1;
        if (a.total_cost_azn_low !== b.total_cost_azn_low) return a.total_cost_azn_low - b.total_cost_azn_low;
        return a.total_months - b.total_months;
      });

    if (preferredDestinations.length === 0) {
      return { mainPlans: sortPlans(activeResult.plans), outsidePlans: [] };
    }

    const main = sortPlans(
      activeResult.plans.filter((p) => preferredDestinations.includes(p.destination_country))
    );
    const outside = sortPlans(
      activeResult.plans.filter((p) => !preferredDestinations.includes(p.destination_country))
    );
    return { mainPlans: main, outsidePlans: outside };
  }, [activeResult, preferredDestinations]);

  // Group plans by status: OPEN vs UNLOCKABLE (D1.3)
  const openPlans = useMemo(() => mainPlans.filter((p) => p.status === "open"), [mainPlans]);
  const unlockablePlans = useMemo(() => mainPlans.filter((p) => p.status === "unlockable"), [mainPlans]);

  // Best outside plans for "Your score goes further here" (D1.4)
  const topOutsidePlans = useMemo(() => {
    const openOutside = outsidePlans.filter((p) => p.status === "open");
    if (openOutside.length > 0) return openOutside;
    return outsidePlans.slice(0, 3);
  }, [outsidePlans]);

  function handleDestinationToggle(code: string) {
    setPreferredDestinations((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  }

  function handleSelectField(fieldValue: string) {
    setFieldOfStudy(fieldValue);
    const match = FIELD_OPTIONS.find((f) => f.value === fieldValue);
    if (match?.dimGroup && !dimGroup) {
      setDimGroup(String(match.dimGroup));
    }
  }

  function handleTargetFromCard(uniName: string) {
    setTargetUniversity(uniName);
    setMode("target");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    const payload: AssessRoutesPayload = {
      level_sought: level,
      qualification_held: qualification,
      gpa: num(gpa),
      gpa_scale: gpa.trim() ? gpaScale : undefined,
      ielts: num(ielts),
      toefl: num(toefl),
      dim_score: num(dim),
      dim_field_group: num(dimGroup),
      sat: num(sat),
      tr_yos: num(trYos), test_as: num(testAs), csca: num(csca), hsk: num(hsk),
      language_certificate_level: language || undefined,
      age: num(age),
      work_experience_hours: num(workHours),
      employer: employer.trim() || undefined,
      budget_azn_per_year: num(budget)
    };

    try {
      const data = await assessRoutes(payload);
      setResult(data);
      setHasSubmitted(true);
    } catch (caught) {
      setError(getUserFacingError(caught, "Route planning"));
      setResult(null);
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      {/* Mode switcher: Discovery vs Target */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div className="inline-flex rounded-full border border-white/10 bg-[#13152c]/90 p-1 backdrop-blur-xl">
          <button
            type="button"
            onClick={() => setMode("discovery")}
            className={`flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold transition-all duration-200 ${
              mode === "discovery"
                ? "bg-gradient-to-r from-purple-500 to-orange-500 text-white shadow-lg shadow-orange-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Compass size={16} aria-hidden="true" />
            Discovery: Explore all routes
          </button>
          <button
            type="button"
            onClick={() => setMode("target")}
            className={`flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold transition-all duration-200 ${
              mode === "target"
                ? "bg-gradient-to-r from-purple-500 to-orange-500 text-white shadow-lg shadow-orange-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Crosshair size={16} aria-hidden="true" />
            Target: Check a university
          </button>
        </div>

        <p className="text-xs text-slate-400">
          {mode === "discovery"
            ? "Enter your credentials to see every reachable route."
            : "Name a university to check its recorded requirements and application steps."}
        </p>
      </div>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,22rem)_1fr] lg:gap-14">
        {/* Profile Sidebar */}
        <form onSubmit={submit} className="rounded-3xl border border-white/10 bg-[#13152c]/85 p-6 backdrop-blur-2xl shadow-2xl h-fit sm:p-7" noValidate>
          <p className="eyebrow">Your profile</p>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Leave anything blank that you do not have. A blank is treated as unknown, never as zero.
          </p>

          {/* D1.1: Level first */}
          <div className="mt-6">
            <label className="field-label" htmlFor="level">I am applying for</label>
            <select
              id="level"
              className="field"
              value={level}
              onChange={(event) => setLevel(event.target.value as "bachelor" | "master")}
            >
              <option value="bachelor" className="bg-[#13152c] text-white">A bachelor&apos;s degree</option>
              <option value="master" className="bg-[#13152c] text-white">A master&apos;s degree</option>
            </select>
            <p className="field-help">
              Level is asked first because findings invert between them: Germany and UK direct entry are closed on attestat but open to bachelor graduates.
            </p>
          </div>

          <div className="mt-5">
            <label className="field-label" htmlFor="qualification">What I hold now</label>
            <select
              id="qualification"
              className="field"
              value={qualification}
              onChange={(event) => setQualification(event.target.value as RouteQualification)}
            >
              {QUALIFICATIONS.map((option) => (
                <option key={option.value} value={option.value} className="bg-[#13152c] text-white">{option.label}</option>
              ))}
            </select>
          </div>

          <div className="mt-5">
            <label className="field-label" htmlFor="gpa">Grade average</label>
            <div className="grid gap-2 sm:grid-cols-[7rem_1fr]">
              <input
                id="gpa"
                className="field"
                inputMode="decimal"
                value={gpa}
                onChange={(event) => setGpa(event.target.value)}
                placeholder="4.6"
              />
              <select
                className="field"
                aria-label="Grade scale"
                value={gpaScale}
                onChange={(event) => setGpaScale(event.target.value as GradeScaleKey)}
              >
                {GRADE_SCALES.map((scale) => (
                  <option key={scale.value} value={scale.value} className="bg-[#13152c] text-white">{scale.label}</option>
                ))}
              </select>
            </div>
            <p className="field-help">
              Pick the scale your grade is actually on. The same number means different things on
              different scales, and a grade without its scale cannot be compared with anything.
            </p>
          </div>

          {/* D1.2: Annual Budget in AZN */}
          <div className="mt-5">
            <label className="field-label" htmlFor="budget">Annual budget (AZN)</label>
            <input
              id="budget"
              className="field"
              inputMode="numeric"
              value={budget}
              onChange={(event) => setBudget(event.target.value)}
              placeholder="e.g. 8000"
            />
            <p className="field-help">
              Recorded for planning. Complete degree-cost ranking remains unavailable while tuition and living-cost data are incomplete.
            </p>
          </div>

          {/* D1.2: Destination Preferences (never excludes) */}
          <div className="mt-5">
            <p className="field-label">Preferred destinations</p>
            <p className="text-xs text-slate-400 mb-2">
              Destination ranks, it never excludes. Chosen countries fill main results; others appear under &ldquo;Your score goes further here&rdquo;.
            </p>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {DESTINATION_OPTIONS.map((dest) => {
                const isSelected = preferredDestinations.includes(dest.code);
                return (
                  <button
                    type="button"
                    key={dest.code}
                    onClick={() => handleDestinationToggle(dest.code)}
                    className={`text-xs p-2.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-orange-500/50 bg-gradient-to-r from-orange-500/20 to-purple-500/20 font-semibold text-orange-300 shadow-[0_0_12px_rgba(255,122,0,0.2)]"
                        : "border-white/10 bg-white/[0.04] text-slate-400 hover:border-white/20 hover:text-white"
                    }`}
                  >
                    {isSelected ? "✓ " : "+ "}
                    {dest.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* D1.2: Field of study */}
          <div className="mt-5">
            <label className="field-label" htmlFor="field-of-study">Field of study</label>
            <select
              id="field-of-study"
              className="field"
              value={fieldOfStudy}
              onChange={(e) => handleSelectField(e.target.value)}
            >
              {FIELD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#13152c] text-white">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <fieldset className="mt-6 border-t border-white/[0.08] pt-5">
            <legend className="sr-only">Exam scores</legend>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Exams you have sat
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {[
                ["ielts", "IELTS", ielts, setIelts, "7.0"],
                ["toefl", "TOEFL (0–120 scale)", toefl, setToefl, "95"],
                ["dim", "DİM", dim, setDim, "560"],
                ["sat", "SAT", sat, setSat, "1350"]
              ].map(([id, label, value, setter, placeholder]) => (
                <div key={id as string}>
                  <label className="field-label" htmlFor={id as string}>{label as string}</label>
                  <input
                    id={id as string}
                    className="field"
                    inputMode="decimal"
                    value={value as string}
                    onChange={(event) => (setter as (v: string) => void)(event.target.value)}
                    placeholder={placeholder as string}
                  />
                </div>
              ))}
            </div>

            <p className="text-xs text-slate-400 mt-2">For a TOEFL result reported on the 1–6 scale, leave TOEFL blank; this planner does not yet compare that scale.</p>

            {dim.trim() !== "" && (
              <div className="mt-4">
                <label className="field-label" htmlFor="dim-group">DİM ixtisas qrupu</label>
                <select
                  id="dim-group"
                  className="field"
                  value={dimGroup}
                  onChange={(event) => setDimGroup(event.target.value)}
                >
                  <option value="" className="bg-[#13152c] text-white">Not sure</option>
                  <option value="1" className="bg-[#13152c] text-white">Group 1 — engineering and technology</option>
                  <option value="2" className="bg-[#13152c] text-white">Group 2</option>
                  <option value="3" className="bg-[#13152c] text-white">Group 3</option>
                  <option value="4" className="bg-[#13152c] text-white">Group 4</option>
                </select>
                <p className="field-help">
                  The state programme asks 400 of Group 1 and 550 of every other field. Leave
                  this blank and any score between the two stays undecided.
                </p>
              </div>
            )}

            <div className="mt-4">
              <label className="field-label" htmlFor="language">Language certificate</label>
              <select
                id="language"
                className="field"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="" className="bg-[#13152c] text-white">None or not sure</option>
                <option value="B2" className="bg-[#13152c] text-white">B2</option>
                <option value="C1" className="bg-[#13152c] text-white">C1</option>
                <option value="C2" className="bg-[#13152c] text-white">C2</option>
              </select>
              <p className="field-help">
                The Dövlət Proqramı requires C1 or above.
              </p>
            </div>
          </fieldset>

          <fieldset className="mt-7 border-t border-white/[0.08] pt-6">
            <legend className="eyebrow">Other admission tests</legend>
            <p className="field-help">Leave tests you have not taken blank. Check the university’s accepted test format and subscores.</p>
            {([
              ["tr-yos", "TR-YÖS", trYos, setTrYos], ["test-as", "TestAS", testAs, setTestAs],
              ["csca", "CSCA", csca, setCsca], ["hsk", "HSK level", hsk, setHsk]
            ] as const).map(([id, label, value, setter]) => <div className="mt-3" key={id}>
              <label className="field-label" htmlFor={id}>{label}</label>
              <input id={id} className="field" inputMode="decimal" value={value} onChange={(event) => setter(event.target.value)} />
            </div>)}
          </fieldset>

          <fieldset className="mt-7 border-t border-white/[0.08] pt-6">
            <legend className="eyebrow">For funding</legend>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Several scholarships are decided by things that have nothing to do with your
              grades. Leave any of these blank and we will say the gate went unchecked —
              never that you cleared it.
            </p>

            <div className="mt-4">
              <label className="field-label" htmlFor="age">Age</label>
              <input
                id="age"
                className="field"
                inputMode="numeric"
                value={age}
                onChange={(event) => setAge(event.target.value)}
                placeholder="e.g. 18"
              />
              <p className="field-help">
                {level === "bachelor"
                  ? "Türkiye Bursları funds bachelor study only for applicants under 21, and it is one of just two scholarships that reach this level at all."
                  : "SOCAR's programme sets an upper age limit; most others do not publish one we have read."}
              </p>
            </div>

            {level === "master" && (
              <>
                <div className="mt-4">
                  <label className="field-label" htmlFor="work-hours">
                    Documented work experience
                  </label>
                  <input
                    id="work-hours"
                    className="field"
                    inputMode="numeric"
                    value={workHours}
                    onChange={(event) => setWorkHours(event.target.value)}
                    placeholder="hours, e.g. 3000"
                  />
                  <p className="field-help">
                    In hours, not years — Chevening asks for 2,800 documented hours and
                    counts part-time and overlapping work against that figure.
                  </p>
                </div>

                <div className="mt-4">
                  <label className="field-label" htmlFor="employer">Employer</label>
                  <input
                    id="employer"
                    className="field"
                    value={employer}
                    onChange={(event) => setEmployer(event.target.value)}
                    placeholder="e.g. SOCAR Downstream"
                  />
                  <p className="field-help">
                    SOCAR gives preference to its own employees and partners. No other
                    academic record opens it, so this is the only way we can tell whether it
                    applies to you.
                  </p>
                </div>
              </>
            )}
          </fieldset>

          <button type="submit" className="button-primary mt-7 w-full shadow-[0_0_25px_rgba(255,107,0,0.35)] min-h-12" disabled={pending}>
            {pending ? (
              <>
                <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                Checking routes
              </>
            ) : (
              <>
                Show my options
                <ArrowRight size={16} aria-hidden="true" />
              </>
            )}
          </button>
        </form>

        {/* Main Content Area */}
        <div aria-live="polite">
          {error && (
            <div className="notice-error">
              <p className="font-semibold">{error.title}</p>
              <p className="mt-1">{error.message}</p>
            </div>
          )}

          {/* TARGET MODE VIEW */}
          {mode === "target" && (
            <CatalogueTarget university={targetUniversity} onUniversity={setTargetUniversity}
              profile={{level_sought: level, qualification_held: qualification,
                ielts: num(ielts), toefl: num(toefl), sat: num(sat), dim_score: num(dim),
                tr_yos: num(trYos), test_as: num(testAs), csca: num(csca), hsk: num(hsk),
                gpa: num(gpa), gpa_scale: gpa.trim() ? gpaScale : undefined}}
              renderUniversity={(row) => <UniversityCard university={row} />} />
          )}

          {/* DISCOVERY MODE VIEW */}
          {mode === "discovery" && activeResult && !error && (
            <>
              {/* Baseline hint if user has not performed a custom submit yet */}
              {!hasSubmitted && (
                <div className="rounded-2xl border border-orange-500/30 bg-orange-500/[0.08] p-4 mb-6 backdrop-blur-md">
                  <p className="body-large text-sm font-semibold text-orange-200">
                    Showing an example for a school-leaver (Attestat, Bachelor), generated 15 September 2026.
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Enter what you hold and what you have scored. You will get every route this
                    qualification opens, what each one costs in time and money, and the universities
                    that document accepting it. Nothing here is a prediction of whether you will be admitted.
                    Requirements are linked to their sources; recognition inferences and unverified facts are labelled.
                  </p>
                </div>
              )}

              {/* Dövlət Proqramı */}
              <div className="rounded-3xl border border-white/10 bg-[#13152c]/85 p-6 sm:p-7 backdrop-blur-2xl shadow-2xl">
                <p className="eyebrow">Dövlət Proqramı</p>
                <h2 className="font-sans text-2xl font-bold text-white mt-2">
                  {activeResult.dp.status === "open"
                    ? "You clear the published requirements"
                    : "Not yet clearing the published requirements"}
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-300">{activeResult.dp.note}</p>

                {activeResult.dp.gates_met.length > 0 && (
                  <ul className="mt-4 space-y-1 text-sm text-emerald-400">
                    {activeResult.dp.gates_met.map((gate) => <li key={gate}>✓ {gate}</li>)}
                  </ul>
                )}
                {activeResult.dp.gates_missing.length > 0 && (
                  <ul className="mt-2 space-y-1 text-sm text-amber-400">
                    {activeResult.dp.gates_missing.map((gate) => <li key={gate}>· {gate}</li>)}
                  </ul>
                )}

                <dl className="mt-5 space-y-3 border-t border-white/[0.08] pt-4 text-xs leading-5">
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.1em] text-slate-400">Places</dt>
                    <dd className="mt-1 text-slate-300">{activeResult.dp.quota_note}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.1em] text-slate-400">When</dt>
                    <dd className="mt-1 text-slate-300">{activeResult.dp.window_note}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.1em] text-slate-400">
                      What you commit to
                    </dt>
                    <dd className="mt-1 text-slate-300">{activeResult.dp.obligation_note}</dd>
                  </div>
                </dl>

                {activeResult.dp.funded_programmes.length > 0 ? (
                  <p className="mt-4 text-sm">
                    <span className="font-semibold text-white">
                      {activeResult.dp.funded_programmes.length} funded programmes
                    </span>{" "}
                    <span className="text-slate-400">
                      in the countries your routes reach. Catalogue years: {[...new Set(activeResult.dp.funded_programmes.map((p) => p.intake_year).filter(Boolean))].join(", ") || "not recorded"}. These entries are not award allocations; funding for another intake needs confirmation.
                    </span>
                  </p>
                ) : (
                  <p className="mt-4 text-sm leading-6 text-slate-400">
                    {activeResult.dp.funded_programmes_explanation}
                  </p>
                )}
              </div>

              {/* D1.3: Results grouped in three groups: OPEN, UNLOCKABLE, BLOCKED */}
              <p className="mt-8 text-sm text-slate-400">
                {activeResult.plans.length} routes, soonest first.
              </p>

              {/* Group 1: OPEN routes */}
              <section className="mt-6">
                <div className="flex items-center gap-3">
                  <h3 className="font-sans text-2xl font-bold text-white">Open Routes</h3>
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">Direct entry</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Routes reachable right now with your current qualifications.
                </p>

                {openPlans.length === 0 ? (
                  <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/50 p-5 mt-3 text-sm text-slate-400">
                    No direct entry routes in your selected destinations are open on this qualification alone.
                    See the unlockable pathways below to open these destinations.
                  </div>
                ) : (
                  openPlans.map((plan, idx) => (
                    <PlanCard
                      key={`open-${plan.hops.map((h) => h.key).join(">")}`}
                      plan={plan}
                      index={idx}
                      budget={num(budget)}
                      onTargetUniversity={handleTargetFromCard}
                    />
                  ))
                )}
              </section>

              {/* Group 2: UNLOCKABLE routes */}
              <section className="mt-10">
                <div className="flex items-center gap-3">
                  <h3 className="font-sans text-2xl font-bold text-white">Unlockable Routes</h3>
                  <span className="rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-orange-400">Pathways available</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Routes that unlock with a preparatory year, foundation programme, or examination.
                </p>

                {unlockablePlans.length === 0 ? (
                  <div className="rounded-2xl border border-white/[0.08] bg-[#101226]/50 p-5 mt-3 text-sm text-slate-400">
                    No unlockable two-hop pathways recorded for these criteria.
                  </div>
                ) : (
                  unlockablePlans.map((plan, idx) => (
                    <PlanCard
                      key={`unlockable-${plan.hops.map((h) => h.key).join(">")}`}
                      plan={plan}
                      index={openPlans.length + idx}
                      budget={num(budget)}
                      onTargetUniversity={handleTargetFromCard}
                    />
                  ))
                )}
              </section>

              {/* D1.4: Persistent "Your score goes further here" section */}
              {preferredDestinations.length > 0 && topOutsidePlans.length > 0 && (
                <section className="mt-12 rounded-3xl border border-purple-500/30 bg-gradient-to-br from-purple-900/20 via-[#13152c]/90 to-orange-950/20 p-6 sm:p-8 backdrop-blur-2xl shadow-2xl">
                  <div className="flex items-center gap-2.5">
                    <Sparkles size={20} className="text-orange-400" />
                    <h3 className="font-sans text-xl sm:text-2xl font-bold text-white">
                      Your score goes further here
                    </h3>
                  </div>
                  <p className="mt-1 text-sm text-slate-300">
                    Destinations you didn&apos;t select where your qualification and scores already clear the bar or unlock pathways.
                    AUSA never excludes options to prevent agency steering.
                  </p>
                  <div className="mt-4 space-y-4">
                    {topOutsidePlans.map((plan, idx) => (
                      <PlanCard
                        key={`outside-${plan.hops.map((h) => h.key).join(">")}`}
                        plan={plan}
                        index={idx}
                        budget={num(budget)}
                        onTargetUniversity={handleTargetFromCard}
                      />
                    ))}
                  </div>
                </section>
              )}

              {/* Prep year trade-off warning */}
              {activeResult.prep_year_warning && (
                <div className="mt-8 rounded-2xl border border-amber-500/20 bg-amber-500/[0.08] p-4 text-amber-200 backdrop-blur-md">
                  <p className="font-semibold text-amber-300">One route costs you another option</p>
                  <p className="mt-2 leading-6 text-sm">{activeResult.prep_year_warning}</p>
                </div>
              )}

              {/* Funding beyond state programme */}
              <section className="mt-10 border-t border-white/[0.08] pt-6">
                <p className="eyebrow">Funding beyond the state programme</p>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {activeResult.scholarships_note}
                </p>
                {activeResult.scholarships.map((scholarship) => (
                  <ScholarshipCard key={scholarship.key} scholarship={scholarship} />
                ))}
              </section>

              {/* Group 3: BLOCKED routes */}
              {activeResult.blocked.length > 0 && (
                <section className="mt-10 border-t border-white/[0.08] pt-6">
                  <p className="eyebrow">Closed to you right now</p>
                  <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-400">
                    {activeResult.blocked.map((entry) => (
                      <li key={entry} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-2 text-slate-400">
                        {entry}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
