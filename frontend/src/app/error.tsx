"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="app-page">
      <div className="panel-strong mx-auto max-w-3xl border-l-4 border-l-danger p-8 sm:p-12" role="alert">
        <p className="eyebrow">Interface error</p>
        <h1 className="page-heading mt-4">This page could not finish rendering.</h1>
        <p className="body-large mt-5">The interface encountered an unexpected error. Retry the page; if it fails again, return home and check the browser console for the recorded error.</p>
        {error.digest && <p className="mt-4 font-mono text-xs text-muted">Error reference: {error.digest}</p>}
        <div className="mt-8 flex flex-wrap gap-3">
          <button type="button" className="button-primary" onClick={reset}><RefreshCw size={17} aria-hidden="true" />Retry page</button>
          <Link className="button-secondary" href="/">Return home</Link>
        </div>
      </div>
    </div>
  );
}
