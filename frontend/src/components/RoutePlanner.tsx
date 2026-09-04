"use client";

import { ArrowRight, ExternalLink, Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { assessRoutes, getUserFacingError } from "@/lib/api";
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
  { value: "a_level", label: "A Levels" },
  { value: "ib", label: "International Baccalaureate" }
];

const GRADE_SCALES: { value: GradeScaleKey; label: string }[] = [
  { value: "5.0", label: "out of 5 — the usual attestat scale" },
  { value: "100", label: "out of 100 — most Azerbaijani and Turkish universities" },
  { value: "4.0", label: "out of 4.0 — US-style GPA" },
  { value: "german", label: "German 1.0–4.0 — where 1.0 is best" }
];

const COUNTRY_NAMES: Record<string, string> = {
  AZ: "Azerbaijan", TR: "Turkey", DE: "Germany", GB: "United Kingdom",
  US: "United States", PL: "Poland", CN: "China"
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

function UniversityCard({ university }: { university: RouteUniversity }) {
  const facts: [string, string][] = [];
  if (university.tuition_per_year !== null) {
    facts.push([
      "Tuition per year",
      `${university.tuition_per_year.toLocaleString("en-US")} ${university.currency ?? ""}`.trim()
    ]);
  }
  if (university.application_deadline) facts.push(["Deadline", university.application_deadline]);
  if (university.language_test) {
    facts.push([
      "Language",
      university.language_minimum_score !== null
        ? `${university.language_test} ${university.language_minimum_score}`
        : `${university.language_test} — no minimum stated`
    ]);
  }
  if (university.entrance_exam) {
    facts.push([
      "Entrance exam",
      university.entrance_exam_minimum !== null
        ? `${university.entrance_exam} ${university.entrance_exam_minimum}`
        : `${university.entrance_exam} — no minimum stated`
    ]);
  }
  if (university.gpa_minimum !== null) {
    facts.push([
      "Minimum grade",
      `${university.gpa_minimum}${university.gpa_scale ? ` out of ${university.gpa_scale}` : ""}`
    ]);
  }
  if (university.application_portal) facts.push(["Apply via", university.application_portal]);

  return (
    <article className="border-t border-quiet py-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h4 className="font-serif text-xl font-semibold">{university.university_name}</h4>
        <span className="text-xs uppercase tracking-[0.12em] text-muted">
          {countryName(university.country_code)} · {university.intake_year} intake
        </span>
      </div>
      <p className="mt-1 text-sm text-muted">{university.program_name}</p>

      {facts.length > 0 && (
        <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {facts.map(([term, value]) => (
            <div key={term} className="flex justify-between gap-3 border-b border-quiet pb-1.5 text-sm">
              <dt className="text-muted">{term}</dt>
              <dd className="text-right font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
      )}

      <GradeLine university={university} />

      {/* The unknowns, said out loud. A blank tuition rendered in a list reads as
          free and a blank language test reads as none required -- both wrong in
          the direction that costs a student an application. */}
      {university.not_stated && (
        <p className="mt-3 text-xs leading-5 text-muted">{university.not_stated}</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
        <a
          className="text-link inline-flex items-center gap-1"
          href={university.source_url}
          target="_blank"
          rel="noreferrer noopener"
        >
          Source page
          <ExternalLink size={12} aria-hidden="true" />
        </a>
        <span>
          {university.provenance === "human-verified"
            ? "Checked by a person"
            : "Read from the source page, not yet checked by a person"}
        </span>
      </div>
    </article>
  );
}

function PlanCard({ plan, index }: { plan: RoutePlan; index: number }) {
  const isOpen = plan.status === "open";

  return (
    <section className="panel mt-6 p-5 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Option {String(index + 1).padStart(2, "0")}</p>
          <h3 className="section-heading mt-2 text-2xl sm:text-3xl">
            {countryName(plan.destination_country)}
          </h3>
        </div>
        <span className={`status-tag ${isOpen ? "status-available" : "status-experimental"}`}>
          {isOpen ? "Open now" : "Needs something first"}
        </span>
      </div>

      <ol className="mt-5 border-y border-quiet">
        {plan.hops.map((hop, hopIndex) => (
          <li key={hop.key} className="flex gap-4 border-b border-quiet py-3 last:border-b-0">
            <span className="font-serif text-lg text-accent">{hopIndex + 1}</span>
            <div className="min-w-0">
              <p className="font-semibold">{hop.mechanism}</p>
              <p className="mt-1 text-xs leading-5 text-muted">
                {countryName(hop.country_code)} · {months(hop.time_cost_months)} ·{" "}
                {money(hop.money_cost_azn_low, hop.money_cost_azn_high)}
              </p>
              {hop.proof_of_funds && (
                <p className="mt-2 border-l-2 border-warning pl-3 text-xs leading-5">
                  <span className="font-semibold">
                    {hop.proof_of_funds.amount.toLocaleString()} {hop.proof_of_funds.currency}{" "}
                    {hop.proof_of_funds.period}, in the bank before the visa.
                  </span>{" "}
                  <span className="text-muted">{hop.proof_of_funds.mechanism}.</span>{" "}
                  <span className="text-muted">
                    This is separate from the cost above — the money stays yours.
                  </span>
                </p>
              )}
              <p className="mt-1 text-xs leading-5 text-muted">{hop.citation}</p>
            </div>
          </li>
        ))}
      </ol>

      <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <div>
          <dt className="text-muted">Extra time</dt>
          <dd className="font-semibold">{months(plan.total_months)}</dd>
        </div>
        <div>
          <dt className="text-muted">Estimated cost</dt>
          <dd className="font-semibold">
            {money(plan.total_cost_azn_low, plan.total_cost_azn_high)}
          </dd>
        </div>
        <div>
          <dt className="text-muted">You would apply holding</dt>
          <dd className="font-semibold">{plan.qualification_delivered.replace(/_/g, " ")}</dd>
        </div>
      </dl>

      {plan.missing.length > 0 && (
        <div className="notice-warning mt-5">
          <p className="font-semibold">Before this route opens:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {plan.missing.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
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
              />
            ))}
          </div>
        ) : (
          /* Never an unexplained empty list. "We have not collected this country"
             and "we collected it and none of them accepts this qualification" are
             different answers and only one of them is about the student. */
          <p className="mt-2 text-sm leading-6 text-muted">{plan.universities_explanation}</p>
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
    <article className="border-t border-quiet py-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h4 className="font-serif text-xl font-semibold">{scholarship.name}</h4>
        <span className="text-xs uppercase tracking-[0.12em] text-muted">
          {TIER_NAMES[scholarship.tier] ?? "Funding"}
          {scholarship.country_code ? ` · ${countryName(scholarship.country_code)}` : ""}
        </span>
      </div>
      <p className="mt-1 text-sm text-muted">{scholarship.provider}</p>

      <p
        className={`mt-3 text-sm font-semibold ${
          scholarship.status === "open"
            ? "text-success"
            : scholarship.status === "blocked"
              ? "text-muted"
              : "text-warning"
        }`}
      >
        {SCHOLARSHIP_HEADLINE[scholarship.status] ?? scholarship.status}
      </p>

      <p className="mt-2 text-sm leading-6">{scholarship.coverage}</p>

      {scholarship.gates_met.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-success">
          {scholarship.gates_met.map((gate) => <li key={gate}>✓ {gate}</li>)}
        </ul>
      )}
      {scholarship.gates_blocked.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm text-muted">
          {scholarship.gates_blocked.map((gate) => <li key={gate}>✕ {gate}</li>)}
        </ul>
      )}
      {scholarship.gates_missing.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm text-warning">
          {scholarship.gates_missing.map((gate) => <li key={gate}>· {gate}</li>)}
        </ul>
      )}

      {/* Rendered apart from the list above, and labelled, because it asks something
          different of the reader. A missing gate is work they can go and do; an unknown
          gate is a fact they can tell us, or a page nobody on this project has read.
          Folding the two together would tell a student to act on a question we never
          actually asked them. */}
      {scholarship.gates_unknown.length > 0 && (
        <div className="mt-3 border-l-2 border-quiet pl-3">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">
            What we could not check
          </p>
          <ul className="mt-1 space-y-1 text-sm leading-6 text-muted">
            {scholarship.gates_unknown.map((gate) => <li key={gate}>{gate}</li>)}
          </ul>
        </div>
      )}

      {scholarship.window && (
        <p className="mt-3 text-xs leading-5 text-muted">
          <span className="font-semibold">When: </span>
          {scholarship.window}
        </p>
      )}
      {scholarship.obligation && (
        <p className="mt-2 text-xs leading-5 text-muted">
          <span className="font-semibold">What you commit to: </span>
          {scholarship.obligation}
        </p>
      )}

      <p className="mt-3 text-xs leading-5 text-muted">
        {scholarship.citation} · {scholarship.provenance}, not yet verified by a person.
      </p>
    </article>
  );
}

export function RoutePlanner() {
  const [level, setLevel] = useState<"bachelor" | "master">("bachelor");
  const [qualification, setQualification] = useState<RouteQualification>("attestat");
  const [gpa, setGpa] = useState("");
  const [gpaScale, setGpaScale] = useState<GradeScaleKey>("5.0");
  const [ielts, setIelts] = useState("");
  const [toefl, setToefl] = useState("");
  const [dim, setDim] = useState("");
  const [dimGroup, setDimGroup] = useState("");
  const [sat, setSat] = useState("");
  const [language, setLanguage] = useState("");
  // The funding inputs. Nothing academic needs them; several scholarships are decided
  // by them alone.
  const [age, setAge] = useState("");
  const [workHours, setWorkHours] = useState("");
  const [employer, setEmployer] = useState("");

  const [result, setResult] = useState<AssessRoutesResponse | null>(null);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);
  const [pending, setPending] = useState(false);

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
      language_certificate_level: language || undefined,
      age: num(age),
      work_experience_hours: num(workHours),
      employer: employer.trim() || undefined
    };

    try {
      setResult(await assessRoutes(payload));
    } catch (caught) {
      setError(getUserFacingError(caught, "Route planning"));
      setResult(null);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,22rem)_1fr] lg:gap-14">
      <form onSubmit={submit} className="panel-strong h-fit p-5 sm:p-6" noValidate>
        <p className="eyebrow">Your profile</p>
        <p className="mt-3 text-sm leading-6 text-muted">
          Leave anything blank that you do not have. A blank is treated as unknown, never as
          zero.
        </p>

        <div className="mt-6">
          <label className="field-label" htmlFor="level">I am applying for</label>
          <select
            id="level"
            className="field"
            value={level}
            onChange={(event) => setLevel(event.target.value as "bachelor" | "master")}
          >
            <option value="bachelor">A bachelor&apos;s degree</option>
            <option value="master">A master&apos;s degree</option>
          </select>
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
              <option key={option.value} value={option.value}>{option.label}</option>
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
                <option key={scale.value} value={scale.value}>{scale.label}</option>
              ))}
            </select>
          </div>
          {/* The scale is not decoration. 4.5 is excellent out of 5 and impossible
              out of 4.0, and nothing but the scale tells them apart. */}
          <p className="field-help">
            Pick the scale your grade is actually on. The same number means different things on
            different scales, and a grade without its scale cannot be compared with anything.
          </p>
        </div>

        <fieldset className="mt-6 border-t border-quiet pt-5">
          <legend className="sr-only">Exam scores</legend>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
            Exams you have sat
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {[
              ["ielts", "IELTS", ielts, setIelts, "7.0"],
              ["toefl", "TOEFL", toefl, setToefl, "95"],
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

          {/* Only asked when it can change an answer. The Dövlət Proqramı's DİM bar is 400
              for Group 1 and 550 for every other field, so without this a score between the
              two cannot be decided either way. */}
          {dim.trim() !== "" && (
            <div className="mt-4">
              <label className="field-label" htmlFor="dim-group">DİM ixtisas qrupu</label>
              <select
                id="dim-group"
                className="field"
                value={dimGroup}
                onChange={(event) => setDimGroup(event.target.value)}
              >
                <option value="">Not sure</option>
                <option value="1">Group 1 — engineering and technology</option>
                <option value="2">Group 2</option>
                <option value="3">Group 3</option>
                <option value="4">Group 4</option>
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
              <option value="">None or not sure</option>
              <option value="B2">B2</option>
              <option value="C1">C1</option>
              <option value="C2">C2</option>
            </select>
            <p className="field-help">
              The Dövlət Proqramı requires C1 or above.
            </p>
          </div>
        </fieldset>

        {/* Funding asks for things nothing academic needs, so they sit in their own
            block with the reason attached. A student who does not see why we want their
            age will assume we are profiling them, and leave it blank. */}
        <fieldset className="mt-7 border-t border-quiet pt-6">
          <legend className="eyebrow">For funding</legend>
          <p className="mt-3 text-sm leading-6 text-muted">
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

          {/* Only asked at master's level, where the awards that use them exist. */}
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
                  placeholder="if you are working"
                />
                <p className="field-help">
                  SOCAR&apos;s scholarship is open only to SOCAR group employees. No
                  academic record opens it, so this is the only way we can tell whether it
                  applies to you.
                </p>
              </div>
            </>
          )}
        </fieldset>

        <button type="submit" className="button-primary mt-7 w-full" disabled={pending}>
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

      <div aria-live="polite">
        {error && (
          <div className="notice-error">
            <p className="font-semibold">{error.title}</p>
            <p className="mt-1">{error.message}</p>
          </div>
        )}

        {!result && !error && (
          <div className="panel p-6 sm:p-8">
            <p className="body-large">
              Enter what you hold and what you have scored. You will get every route this
              qualification opens, what each one costs in time and money, and the universities
              that document accepting it.
            </p>
            <p className="mt-4 text-sm leading-6 text-muted">
              Nothing here is a prediction of whether you will be admitted. Every requirement
              shown is quoted from a university&apos;s own page and linked back to it.
            </p>
          </div>
        )}

        {result && (
          <>
            <div className="panel-strong p-5 sm:p-6">
              <p className="eyebrow">Dövlət Proqramı</p>
              <h2 className="section-heading mt-2 text-2xl">
                {result.dp.status === "open"
                  ? "You clear the published requirements"
                  : "Not yet clearing the published requirements"}
              </h2>
              <p className="mt-3 text-sm leading-6 text-muted">{result.dp.note}</p>

              {result.dp.gates_met.length > 0 && (
                <ul className="mt-4 space-y-1 text-sm text-success">
                  {result.dp.gates_met.map((gate) => <li key={gate}>✓ {gate}</li>)}
                </ul>
              )}
              {result.dp.gates_missing.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm text-warning">
                  {result.dp.gates_missing.map((gate) => <li key={gate}>· {gate}</li>)}
                </ul>
              )}

              {/* Not gates, and deliberately shown whether or not the gates are cleared.
                  A student who clears everything still needs to know they are joining a
                  queue of 125 places, signing a five-year return contract, and applying
                  for an academic year that is not the one they assumed. */}
              <dl className="mt-5 space-y-3 border-t border-quiet pt-4 text-xs leading-5">
                <div>
                  <dt className="font-semibold uppercase tracking-[0.1em] text-muted">Places</dt>
                  <dd className="mt-1">{result.dp.quota_note}</dd>
                </div>
                <div>
                  <dt className="font-semibold uppercase tracking-[0.1em] text-muted">When</dt>
                  <dd className="mt-1">{result.dp.window_note}</dd>
                </div>
                <div>
                  <dt className="font-semibold uppercase tracking-[0.1em] text-muted">
                    What you commit to
                  </dt>
                  <dd className="mt-1">{result.dp.obligation_note}</dd>
                </div>
              </dl>

              {result.dp.funded_programmes.length > 0 ? (
                <p className="mt-4 text-sm">
                  <span className="font-semibold">
                    {result.dp.funded_programmes.length} funded programmes
                  </span>{" "}
                  <span className="text-muted">
                    in the countries your routes reach.
                  </span>
                </p>
              ) : (
                <p className="mt-4 text-sm leading-6 text-muted">
                  {result.dp.funded_programmes_explanation}
                </p>
              )}
            </div>

            {result.plans.length === 0 ? (
              <div className="notice-warning mt-6">
                <p>
                  No route in our list is currently reachable with that qualification at this
                  level. That is not a statement that no path exists — only that none of the
                  routes we hold opens on it.
                </p>
              </div>
            ) : (
              <>
                <p className="mt-8 text-sm text-muted">
                  {result.plans.length} routes, soonest first.
                </p>
                {result.plans.map((plan, index) => (
                  <PlanCard key={plan.hops.map((h) => h.key).join(">")} plan={plan} index={index} />
                ))}
              </>
            )}

            {/* The one thing on this page that needs two models at once: the prep year
                opens Germany and the UK, and spends the twelve months that can push a
                student past Türkiye Bursları' under-21 bachelor limit. Placed between
                the routes and the funding because it belongs to both. */}
            {result.prep_year_warning && (
              <div className="notice-warning mt-8">
                <p className="font-semibold">One route costs you another option</p>
                <p className="mt-2 leading-6">{result.prep_year_warning}</p>
              </div>
            )}

            <section className="mt-10 border-t border-line pt-6">
              <p className="eyebrow">Funding beyond the state programme</p>
              <p className="mt-3 text-sm leading-6 text-muted">
                {result.scholarships_note}
              </p>
              {result.scholarships.map((scholarship) => (
                <ScholarshipCard key={scholarship.key} scholarship={scholarship} />
              ))}
            </section>

            {result.blocked.length > 0 && (
              <section className="mt-10 border-t border-line pt-6">
                <p className="eyebrow">Closed to you right now</p>
                <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
                  {result.blocked.map((entry) => <li key={entry}>{entry}</li>)}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
