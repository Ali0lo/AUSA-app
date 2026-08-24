import { FeatureState } from "@/types";

const labels: Record<FeatureState, string> = {
  available: "Available",
  demo: "Demo",
  experimental: "Experimental",
  unavailable: "Unavailable",
  offline: "Offline"
};

export function FeatureTag({ state, label }: { state: FeatureState; label?: string }) {
  return <span className={`status-tag status-${state}`}>{label || labels[state]}</span>;
}
