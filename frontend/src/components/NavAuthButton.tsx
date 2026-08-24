"use client";

import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function NavAuthButton({ mobile = false }: { mobile?: boolean }) {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [error, setError] = useState("");

  if (status === "loading") {
    return <span className="text-xs text-muted" role="status">Checking session</span>;
  }

  if (!session) {
    return (
      <div className={`flex ${mobile ? "w-full flex-col" : "items-center"} gap-2`}>
        <Link href="/sign-in" className={mobile ? "button-secondary w-full" : "button-secondary"}>
          Sign in
        </Link>
        <Link href="/register" className={mobile ? "button-primary w-full" : "button-primary"}>
          Create account
        </Link>
      </div>
    );
  }

  async function endSession() {
    setIsSigningOut(true);
    setError("");

    try {
      const result = await signOut({ callbackUrl: "/", redirect: false });
      const url = new URL(result.url || "/", window.location.origin);
      const destination = url.origin === window.location.origin ? `${url.pathname}${url.search}${url.hash}` : "/";
      router.push(destination);
      router.refresh();
    } catch {
      setError("Sign-out failed. The current session remains active.");
      setIsSigningOut(false);
    }
  }

  return (
    <div className={`flex ${mobile ? "w-full flex-col items-start" : "items-center"} gap-3`}>
      <span className="max-w-44 truncate text-xs text-muted">{session.user?.email}</span>
      <button
        type="button"
        className={mobile ? "button-secondary w-full" : "button-secondary"}
        disabled={isSigningOut}
        onClick={() => void endSession()}
      >
        {isSigningOut ? "Signing out" : "Sign out"}
      </button>
      {error && <span className="max-w-52 text-xs font-semibold text-danger" role="alert">{error}</span>}
    </div>
  );
}
