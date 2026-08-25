import { ReactNode } from "react";

type NoticeTone = "info" | "success" | "warning" | "error";

export function Notice({
  title,
  children,
  tone = "info",
  live = false
}: {
  title: string;
  children: ReactNode;
  tone?: NoticeTone;
  live?: boolean;
}) {
  return (
    <div
      className={`notice notice-${tone}`}
      role={tone === "error" ? "alert" : live ? "status" : undefined}
      aria-live={live ? "polite" : undefined}
    >
      <p className="font-semibold text-ink">{title}</p>
      <div className="mt-1 text-muted">{children}</div>
    </div>
  );
}
