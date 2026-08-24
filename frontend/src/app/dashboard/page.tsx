"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/match");
  }, [router]);

  return (
    <div className="app-page" role="status" aria-live="polite">
      <div className="panel mx-auto max-w-2xl p-8">
        <p className="eyebrow">Route updated</p>
        <h1 className="mt-3 font-serif text-3xl font-semibold">Opening the matching workspace.</h1>
        <p className="mt-4 text-muted">The earlier dashboard route now maps to matching. <Link className="text-link" href="/match">Open matching directly.</Link></p>
      </div>
    </div>
  );
}
