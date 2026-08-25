import type { Metadata } from "next";
import { SignInForm } from "@/components/SignInForm";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AUSA with an existing student account."
};

export default async function SignInPage({
  searchParams
}: {
  searchParams: Promise<{ callbackUrl?: string; email?: string; error?: string }>;
}) {
  const parameters = await searchParams;
  const initialError = parameters.error
    ? "The authentication session could not be completed. Try signing in again."
    : undefined;

  return (
    <SignInForm
      callbackUrl={parameters.callbackUrl}
      initialEmail={parameters.email}
      initialError={initialError}
    />
  );
}
