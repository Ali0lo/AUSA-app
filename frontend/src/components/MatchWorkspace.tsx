"use client";

import { useSession } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { FeatureTag } from "@/components/FeatureTag";
import { MatchCard } from "@/components/MatchCard";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { fetchCurrentStudentProfile, fetchMatchScore, getUserFacingError, UserFacingError } from "@/lib/api";
import { DEMO_PROGRAMS, getDemoProgram } from "@/lib/demo-programs";
import { formatMoney } from "@/lib/format";
import { DegreeLevel, MatchResult, StudentProfile } from "@/types";

const defaultProfile: StudentProfile = {
  gpa: 3.6,
  budget: 18000,
  ielts: 7,
  toefl: 98,
  degree_level: "master",
  field_of_study: "Computer Science"
};

function optionalNumber(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function MatchWorkspace() {
  const searchParams = useSearchParams();
  const { data: session, status: sessionStatus } = useSession();
  const requestedProgram = getDemoProgram(searchParams.get("program"));
  const [profile, setProfile] = useState<StudentProfile>(defaultProfile);
  const [selectedProgramId, setSelectedProgramId] = useState<number>(requestedProgram?.program_id || 101);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<UserFacingError | null>(null);
  const [profileNotice, setProfileNotice] = useState<UserFacingError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadedProfileToken, setLoadedProfileToken] = useState<string | null>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const token = session?.user?.accessToken;
  const isLoadingProfile = sessionStatus === "loading" || Boolean(token && loadedProfileToken !== token);

  const selectedProgram = useMemo(
    () => DEMO_PROGRAMS.find((program) => program.program_id === selectedProgramId) || DEMO_PROGRAMS[0],
    [selectedProgramId]
  );

  useEffect(() => {
    if (!token) return;
    let active = true;

    fetchCurrentStudentProfile(token)
      .then((student) => {
        if (!active) return;
        setProfile({
          gpa: student.gpa,
          budget: student.budget,
          ielts: student.ielts ?? undefined,
          toefl: student.toefl ?? undefined,
          degree_level: student.degree_level,
          field_of_study: student.field_of_study,
          research_experience: student.research_experience
        });
        setProfileNotice(null);
      })
      .catch((loadError) => {
        if (active) setProfileNotice(getUserFacingError(loadError, "Profile loading"));
      })
      .finally(() => {
        if (active) setLoadedProfileToken(token);
      });

    return () => {
      active = false;
    };
  }, [token]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetchMatchScore(profile, selectedProgram, session?.user?.accessToken);
      setResult(response);
    } catch (submitError) {
      setError(getUserFacingError(submitError, "Prototype matching"));
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateProfile<K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) {
    setProfile((current) => ({ ...current, [key]: value }));
    setResult(null);
    setError(null);
  }

  function resetProfile() {
    setProfile(defaultProfile);
    setResult(null);
    setError(null);
    setProfileNotice(null);
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Compatibility evaluator</p>
            <FeatureTag state="demo" label="Prototype scoring" />
          </div>
          <h1 className="page-heading mt-4">Compare a profile with programme requirements.</h1>
          <p className="body-large mt-5">
            This interface sends the original student and programme payloads to <code className="font-mono text-sm text-ink">/matching/evaluate</code> and presents the response without changing its meaning.
          </p>
        </div>
        <ServiceStatus />
      </div>

      {sessionStatus !== "loading" && !session && (
        <div className="mt-7">
          <Notice title="Manual profile mode">
            You can use matching without an account. Sign in if you want the form to load the student profile stored by the backend.
          </Notice>
        </div>
      )}

      {profileNotice && (
        <div className="mt-7">
          <Notice title={profileNotice.title} tone="warning" live>{profileNotice.message} The manual form remains available.</Notice>
        </div>
      )}

      <div className="mt-10 grid gap-8 xl:grid-cols-[0.85fr_1.15fr] xl:items-start">
        <form ref={formRef} onSubmit={submit} className="panel-strong scroll-mt-28 p-6 sm:p-8" aria-label="Student matching profile">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
            <div>
              <h2 className="font-serif text-2xl font-semibold">Student profile</h2>
              <p className="mt-1 text-sm text-muted">Required values match the existing backend schema.</p>
            </div>
            <button type="button" className="text-link min-h-10" onClick={resetProfile}>Reset form</button>
          </div>

          <fieldset className="mt-7 grid gap-5 sm:grid-cols-2" disabled={isSubmitting || isLoadingProfile}>
            <legend className="sr-only">Student academic and financial information</legend>
            <div>
              <label className="field-label" htmlFor="gpa">GPA on a 4.0 scale</label>
              <input
                id="gpa"
                className="field"
                type="number"
                required
                min="0"
                max="4"
                step="0.01"
                value={profile.gpa}
                onChange={(event) => updateProfile("gpa", Number(event.target.value))}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="budget">Annual tuition budget</label>
              <input
                id="budget"
                className="field"
                type="number"
                required
                min="0"
                step="100"
                value={profile.budget}
                onChange={(event) => updateProfile("budget", Number(event.target.value))}
              />
              <p className="field-help">The current backend compares this number directly with programme tuition and does not convert currencies.</p>
            </div>
            <div>
              <label className="field-label" htmlFor="ielts">IELTS score</label>
              <input
                id="ielts"
                className="field"
                type="number"
                min="0"
                max="9"
                step="0.5"
                value={profile.ielts ?? ""}
                onChange={(event) => updateProfile("ielts", optionalNumber(event.target.value))}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="toefl">TOEFL iBT score</label>
              <input
                id="toefl"
                className="field"
                type="number"
                min="0"
                max="120"
                step="1"
                value={profile.toefl ?? ""}
                onChange={(event) => updateProfile("toefl", optionalNumber(event.target.value))}
              />
              <p className="field-help">Provide IELTS, TOEFL, or both.</p>
            </div>
            <div>
              <label className="field-label" htmlFor="degree-level">Target degree</label>
              <select
                id="degree-level"
                className="field"
                value={profile.degree_level}
                onChange={(event) => updateProfile("degree_level", event.target.value as DegreeLevel)}
              >
                <option value="bachelor">Bachelor</option>
                <option value="master">Master</option>
                <option value="phd">PhD</option>
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="field-of-study">Field of study</label>
              <input
                id="field-of-study"
                className="field"
                type="text"
                value={profile.field_of_study || ""}
                onChange={(event) => updateProfile("field_of_study", event.target.value)}
              />
              <p className="field-help">Sent in the request; the current prototype score does not use it.</p>
            </div>
          </fieldset>

          <div className="mt-9 border-t border-line pt-7">
            <h2 className="font-serif text-2xl font-semibold">Demo programme</h2>
            <p className="mt-2 text-sm leading-6 text-muted">The backend has no programme-list endpoint yet, so the original three frontend records remain the selectable catalogue.</p>
            <div className="mt-5 space-y-3">
              {DEMO_PROGRAMS.map((program) => {
                const selected = program.program_id === selectedProgramId;
                return (
                  <button
                    key={program.program_id}
                    type="button"
                    className={`w-full border p-4 text-left transition-colors ${selected ? "border-accent bg-[#f7e9e0]" : "border-quiet bg-paper hover:border-line"}`}
                    aria-pressed={selected}
                    onClick={() => {
                      setSelectedProgramId(program.program_id || 101);
                      setResult(null);
                      setError(null);
                    }}
                    disabled={isSubmitting}
                  >
                    <span className="flex flex-wrap items-start justify-between gap-3">
                      <span>
                        <span className="block font-serif text-lg font-semibold">{program.program_name}</span>
                        <span className="mt-1 block text-sm text-muted">{program.university_name}</span>
                      </span>
                      <span className="text-sm font-semibold">{formatMoney(program.tuition_fee, program.currency)}</span>
                    </span>
                    <span className="mt-3 block text-xs text-muted">
                      {program.degree_level.toUpperCase()} · {program.country} · GPA {program.min_gpa ?? "not stated"} · IELTS {program.min_ielts ?? "not stated"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <button type="submit" className="button-primary mt-7 w-full" disabled={isSubmitting || isLoadingProfile}>
            {isSubmitting ? "Evaluating with backend" : "Evaluate compatibility"}
          </button>
        </form>

        <div aria-live="polite">
          {error && (
            <div className="panel-strong p-6 sm:p-8">
              <Notice title={error.title} tone="error" live>{error.message}</Notice>
              <button type="button" className="button-secondary mt-5" onClick={() => formRef.current?.requestSubmit()} disabled={isSubmitting}>Try again</button>
            </div>
          )}

          {!error && result && (
            <MatchCard
              result={result}
              onReset={() => {
                setResult(null);
                formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
            />
          )}

          {!error && !result && (
            <div className="panel-strong p-7 sm:p-10">
              <FeatureTag state="demo" label="Awaiting evaluation" />
              <h2 className="mt-5 font-serif text-3xl font-semibold">Your backend response will appear here.</h2>
              <p className="mt-4 max-w-xl leading-7 text-muted">
                Review the profile and selected programme, then run the evaluation. If the endpoint is unavailable, this area will report the exact failure instead of inventing a result.
              </p>
              <dl className="mt-8 grid gap-5 border-t border-line pt-6 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Selected programme</dt>
                  <dd className="mt-2 font-serif text-xl font-semibold">{selectedProgram.program_name}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Target degree</dt>
                  <dd className="mt-2 font-serif text-xl font-semibold capitalize">{profile.degree_level}</dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
