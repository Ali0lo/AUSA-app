"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";

function safeDestination(value: string): string {
  return value.startsWith("/") && !value.startsWith("//") ? value : "/match";
}

function resultDestination(value: string | null, fallback: string): string {
  if (!value) return fallback;

  try {
    const url = new URL(value, window.location.origin);
    return url.origin === window.location.origin ? `${url.pathname}${url.search}${url.hash}` : fallback;
  } catch {
    return fallback;
  }
}

export function SignInForm({
  initialEmail = "",
  callbackUrl = "/match",
  initialError
}: {
  initialEmail?: string;
  callbackUrl?: string;
  initialError?: string;
}) {
  const router = useRouter();
  const { status } = useSession();
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [error, setError] = useState(initialError || "");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace(safeDestination(callbackUrl));
  }, [callbackUrl, router, status]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const destination = safeDestination(callbackUrl);
      const result = await signIn("credentials", {
        email: email.trim(),
        password,
        callbackUrl: destination,
        redirect: false
      });

      if (!result || result.error) {
        setError(
          "The backend did not accept this sign-in attempt. Check the email and password. The backend status above will show if the service is offline."
        );
        return;
      }

      router.push(resultDestination(result.url, destination));
      router.refresh();
    } catch {
      setError("Sign-in could not be completed because the authentication service did not return a usable response.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-page">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
        <div className="pt-3">
          <p className="eyebrow">Student account</p>
          <h1 className="page-heading mt-4">Sign in to load your saved profile.</h1>
          <p className="body-large mt-5">
            Authentication uses the existing backend credentials endpoint. Matching remains available in manual mode without an account.
          </p>
          <div className="mt-7">
            <ServiceStatus />
          </div>
        </div>

        <form className="panel-strong p-6 sm:p-8" onSubmit={submit} aria-label="Sign in">
          <h2 className="font-serif text-2xl font-semibold">Account credentials</h2>
          <p className="mt-2 text-sm leading-6 text-muted">Use an account registered with this AUSA backend.</p>

          {error && (
            <div className="mt-6">
              <Notice title="Sign-in failed" tone="error" live>{error}</Notice>
            </div>
          )}

          <div className="mt-7">
            <label className="field-label" htmlFor="sign-in-email">Email address</label>
            <input
              id="sign-in-email"
              className="field"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="mt-5">
            <label className="field-label" htmlFor="sign-in-password">Password</label>
            <input
              id="sign-in-password"
              className="field"
              type="password"
              autoComplete="current-password"
              required
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <button type="submit" className="button-primary mt-7 w-full" disabled={submitting || status === "loading"}>
            {submitting ? "Signing in" : "Sign in"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </button>

          <p className="mt-6 border-t border-quiet pt-5 text-sm text-muted">
            No account yet? <Link className="text-link" href="/register">Create one with a student profile.</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
