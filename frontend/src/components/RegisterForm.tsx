"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { getUserFacingError, registerStudent, UserFacingError } from "@/lib/api";
import { DegreeLevel, RegisterPayload } from "@/types";

const initialProfile: RegisterPayload = {
  email: "",
  password: "",
  gpa: 4.5,
  gpa_scale: "5.0",
  budget: 15000,
  ielts: 7,
  toefl: 95,
  degree_level: "master",
  field_of_study: "Computer Science",
  country: "Azerbaijan"
};

function optionalNumber(value: string): number | undefined {
  return value.trim() ? Number(value) : undefined;
}

export function RegisterForm() {
  const router = useRouter();
  const { status } = useSession();
  const [profile, setProfile] = useState(initialProfile);
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<UserFacingError | null>(null);
  const [created, setCreated] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/plan");
  }, [router, status]);

  function update<K extends keyof RegisterPayload>(key: K, value: RegisterPayload[K]) {
    setProfile((current) => ({ ...current, [key]: value }));
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setCreated(false);

    if (profile.password !== confirmation) {
      setError({ title: "Passwords do not match", message: "Enter the same password in both password fields." });
      return;
    }

    setSubmitting(true);

    try {
      await registerStudent({
        ...profile,
        email: profile.email.trim(),
        field_of_study: profile.field_of_study?.trim() || undefined,
        country: profile.country?.trim() || undefined
      });
      setCreated(true);

      const result = await signIn("credentials", {
        email: profile.email.trim(),
        password: profile.password,
        callbackUrl: "/plan",
        redirect: false
      });

      if (!result || result.error) {
        setError({
          title: "Account created; sign-in incomplete",
          message: "The backend created the account, but the session could not be started. Open the sign-in page and use the same credentials."
        });
        return;
      }

      router.push("/plan");
      router.refresh();
    } catch (submitError) {
      setError(getUserFacingError(submitError, "Account creation"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className="eyebrow">Student account</p>
          <h1 className="page-heading mt-4">Create a profile the backend can reuse.</h1>
          <p className="body-large mt-5">
            These are the fields accepted by the existing registration endpoint. A successful registration starts a session and opens matching.
          </p>
        </div>
        <ServiceStatus />
      </div>

      <form className="panel-strong mx-auto mt-10 max-w-4xl p-6 sm:p-8" onSubmit={submit} aria-label="Create account">
        {error && (
          <div className="mb-7">
            <Notice title={error.title} tone={created ? "warning" : "error"} live>
              {error.message}{created && <> <Link className="text-link" href={`/sign-in?email=${encodeURIComponent(profile.email)}`}>Open sign in.</Link></>}
            </Notice>
          </div>
        )}

        <fieldset disabled={submitting}>
          <legend className="font-serif text-2xl font-semibold">Credentials</legend>
          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="field-label" htmlFor="register-email">Email address</label>
              <input id="register-email" className="field" type="email" autoComplete="email" required value={profile.email} onChange={(event) => update("email", event.target.value)} />
            </div>
            <div>
              <label className="field-label" htmlFor="register-password">Password</label>
              <input id="register-password" className="field" type="password" autoComplete="new-password" required minLength={6} value={profile.password} onChange={(event) => update("password", event.target.value)} />
              <p className="field-help">Use at least six characters, as required by the backend contract.</p>
            </div>
            <div>
              <label className="field-label" htmlFor="register-confirmation">Confirm password</label>
              <input id="register-confirmation" className="field" type="password" autoComplete="new-password" required minLength={6} value={confirmation} onChange={(event) => { setConfirmation(event.target.value); setError(null); }} />
            </div>
          </div>
        </fieldset>

        <fieldset className="mt-9 border-t border-line pt-7" disabled={submitting}>
          <legend className="font-serif text-2xl font-semibold">Academic profile</legend>
          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <div>
              <label className="field-label" htmlFor="register-gpa">Grade average</label>
              <input id="register-gpa" className="field" type="number" required min="0" step="0.01" value={profile.gpa} onChange={(event) => update("gpa", Number(event.target.value))} />
            </div>
            <div>
              {/* Asked, never assumed. The form used to hardcode "GPA on a 4.0 scale" and
                  cap the input at 4, which rejected the 4.5-out-of-5 attestat most of our
                  users actually hold. */}
              <label className="field-label" htmlFor="register-gpa-scale">Which scale is that on?</label>
              <select id="register-gpa-scale" className="field" required value={profile.gpa_scale} onChange={(event) => update("gpa_scale", event.target.value)}>
                <option value="5.0">Out of 5 — Azerbaijani attestat</option>
                <option value="100">Out of 100 — Azerbaijani or Turkish university</option>
                <option value="4.0">Out of 4.0 — US-style GPA</option>
                <option value="german">German 1.0–4.0 — lower is better</option>
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="register-budget">Annual tuition budget</label>
              <input id="register-budget" className="field" type="number" required min="0" step="100" value={profile.budget} onChange={(event) => update("budget", Number(event.target.value))} />
            </div>
            <div>
              <label className="field-label" htmlFor="register-ielts">IELTS score</label>
              <input id="register-ielts" className="field" type="number" min="0" max="9" step="0.5" value={profile.ielts ?? ""} onChange={(event) => update("ielts", optionalNumber(event.target.value))} />
            </div>
            <div>
              <label className="field-label" htmlFor="register-toefl">TOEFL iBT score</label>
              <input id="register-toefl" className="field" type="number" min="0" max="120" step="1" value={profile.toefl ?? ""} onChange={(event) => update("toefl", optionalNumber(event.target.value))} />
            </div>
            <div>
              <label className="field-label" htmlFor="register-degree">Target degree</label>
              <select id="register-degree" className="field" value={profile.degree_level} onChange={(event) => update("degree_level", event.target.value as DegreeLevel)}>
                <option value="bachelor">Bachelor</option>
                <option value="master">Master</option>
                <option value="phd">PhD</option>
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="register-field">Field of study</label>
              <input id="register-field" className="field" type="text" maxLength={100} value={profile.field_of_study || ""} onChange={(event) => update("field_of_study", event.target.value)} />
            </div>
            <div className="sm:col-span-2">
              <label className="field-label" htmlFor="register-country">Country</label>
              <input id="register-country" className="field" type="text" maxLength={50} value={profile.country || ""} onChange={(event) => update("country", event.target.value)} />
            </div>
          </div>
        </fieldset>

        <div className="mt-8 flex flex-col-reverse gap-4 border-t border-quiet pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted">Already registered? <Link className="text-link" href="/sign-in">Sign in.</Link></p>
          <button type="submit" className="button-primary" disabled={submitting || status === "loading"}>
            {submitting ? "Creating account" : "Create account"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </button>
        </div>
      </form>
    </div>
  );
}
