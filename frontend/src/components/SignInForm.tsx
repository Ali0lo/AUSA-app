"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";

function safeDestination(value: string): string {
  return value.startsWith("/") && !value.startsWith("//") ? value : "/plan";
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
  callbackUrl = "/plan",
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
            Authentication uses the existing backend credentials endpoint or Google OAuth. Matching remains available in manual mode without an account.
          </p>
          <div className="mt-7">
            <ServiceStatus />
          </div>
        </div>

        <form className="panel-strong p-6 sm:p-8" onSubmit={submit} aria-label="Sign in">
          <h2 className="font-serif text-2xl font-semibold">Account credentials</h2>
          <p className="mt-2 text-sm leading-6 text-muted">Use an account registered with this AUSA backend or your Google account.</p>

          {error && (
            <div className="mt-6">
              <Notice title="Sign-in failed" tone="error" live>{error}</Notice>
            </div>
          )}

          <div className="mt-6">
            <button
              type="button"
              className="button-secondary w-full flex items-center justify-center gap-3 py-3"
              onClick={() => void signIn("google", { callbackUrl: safeDestination(callbackUrl) })}
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Sign in with Google</span>
            </button>
          </div>

          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 border-t border-quiet" />
            <span className="text-xs uppercase tracking-wider text-muted">Or sign in with email</span>
            <div className="flex-1 border-t border-quiet" />
          </div>

          <div>
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
