"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import { FeatureTag } from "@/components/FeatureTag";

type CheckState = "checking" | "online" | "offline";

export function ServiceStatus() {
  const [state, setState] = useState<CheckState>("checking");
  const [version, setVersion] = useState<string | null>(null);

  async function check() {
    setState("checking");
    try {
      const health = await fetchHealth();
      setVersion(health.version);
      setState("online");
    } catch {
      setVersion(null);
      setState("offline");
    }
  }

  useEffect(() => {
    let active = true;

    fetchHealth()
      .then((health) => {
        if (!active) return;
        setVersion(health.version);
        setState("online");
      })
      .catch(() => {
        if (!active) return;
        setVersion(null);
        setState("offline");
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-3" role="status" aria-live="polite">
      {state === "checking" && <FeatureTag state="experimental" label="Checking backend" />}
      {state === "online" && <FeatureTag state="available" label={`Backend online${version ? ` · v${version}` : ""}`} />}
      {state === "offline" && <FeatureTag state="offline" label="Backend offline" />}
      <button
        type="button"
        className="inline-flex min-h-9 items-center gap-2 border-b border-ink px-1 text-xs font-semibold text-ink hover:text-accent"
        onClick={() => void check()}
        disabled={state === "checking"}
      >
        <RefreshCw size={14} aria-hidden="true" />
        {state === "checking" ? "Checking" : "Check again"}
      </button>
    </div>
  );
}
