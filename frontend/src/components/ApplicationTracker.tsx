"use client";

import { AlertCircle, Calendar, Clock, MapPin } from "lucide-react";
import { useState } from "react";
import { updateTrackedApplicationStage } from "@/lib/api";
import { TrackedApplication } from "@/types";

interface ApplicationTrackerProps {
  initialApplications: TrackedApplication[];
  token?: string;
  onRefresh?: () => void;
}

const STAGE_COLUMNS = [
  { id: "shortlisted", label: "Shortlisted", color: "border-quiet bg-[#fcfbfa]" },
  { id: "preparing_documents", label: "Docs in Progress", color: "border-accent/40 bg-[#fbf9f4]" },
  { id: "submitted", label: "Submitted", color: "border-info/40 bg-[#f4f7fb]" },
  { id: "decision", label: "Decision Received", color: "border-success/40 bg-[#f3f9f4]" }
];

export function ApplicationTracker({ initialApplications, token, onRefresh }: ApplicationTrackerProps) {
  const [applications, setApplications] = useState<TrackedApplication[]>(initialApplications);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  async function handleStageChange(appId: number, nextStage: string) {
    setUpdatingId(appId);
    try {
      const updated = await updateTrackedApplicationStage(appId, nextStage, undefined, token);
      setApplications((current) =>
        current.map((item) => (item.id === appId ? { ...item, stage: updated.stage } : item))
      );
      if (onRefresh) onRefresh();
    } catch {
      setApplications((current) =>
        current.map((item) => (item.id === appId ? { ...item, stage: nextStage } : item))
      );
    } finally {
      setUpdatingId(null);
    }
  }

  function getAppsForColumn(columnId: string): TrackedApplication[] {
    if (columnId === "decision") {
      return applications.filter((app) => app.stage === "accepted" || app.stage === "rejected" || app.stage === "decision");
    }
    return applications.filter((app) => app.stage === columnId);
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {STAGE_COLUMNS.map((col) => {
          const colApps = getAppsForColumn(col.id);
          return (
            <div key={col.id} className={`panel-strong border ${col.color} p-4 sm:p-5 flex flex-col min-h-[500px]`}>
              <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
                <h3 className="font-serif text-lg font-semibold text-ink">{col.label}</h3>
                <span className="flex h-6 w-6 items-center justify-center border border-ink text-xs font-semibold bg-paper">
                  {colApps.length}
                </span>
              </div>

              <div className="flex-1 space-y-4 overflow-y-auto">
                {colApps.length === 0 ? (
                  <div className="border border-dashed border-quiet p-4 text-center text-xs text-muted">
                    No programs in this stage.
                  </div>
                ) : (
                  colApps.map((app) => (
                    <article key={app.id} className="border border-quiet bg-paper p-4 shadow-sm hover:border-accent transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-[0.68rem] font-semibold uppercase tracking-wider text-accent border border-accent/30 px-1.5 py-0.5">
                          {app.degree_level || "Master"}
                        </span>
                        {app.is_urgent ? (
                          <span className="inline-flex items-center gap-1 text-[0.65rem] font-bold uppercase tracking-wider bg-danger text-paper px-2 py-0.5">
                            <AlertCircle size={10} />
                            {app.days_remaining}d left
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[0.65rem] font-semibold text-muted bg-[#f4efe6] px-2 py-0.5">
                            <Clock size={10} />
                            {app.days_remaining} days
                          </span>
                        )}
                      </div>

                      <h4 className="mt-3 font-serif text-lg font-semibold leading-tight text-ink">
                        {app.program_name}
                      </h4>
                      <p className="mt-1 text-xs font-semibold text-muted">{app.university_name}</p>

                      <div className="mt-3 flex items-center justify-between text-xs text-muted border-t border-quiet pt-2">
                        <span className="inline-flex items-center gap-1">
                          <MapPin size={12} />
                          {app.country || "International"}
                        </span>
                        {app.deadline && (
                          <span className="inline-flex items-center gap-1">
                            <Calendar size={12} />
                            {app.deadline}
                          </span>
                        )}
                      </div>

                      {app.notes && (
                        <p className="mt-2 text-xs italic leading-5 text-muted border-l-2 border-accent/50 pl-2">
                          &quot;{app.notes}&quot;
                        </p>
                      )}

                      <div className="mt-4 border-t border-quiet pt-3">
                        <label className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted block mb-1">
                          Move Stage:
                        </label>
                        <select
                          className="field py-1 text-xs"
                          value={app.stage}
                          disabled={updatingId === app.id}
                          onChange={(e) => void handleStageChange(app.id, e.target.value)}
                        >
                          <option value="shortlisted">Shortlisted</option>
                          <option value="preparing_documents">Docs in Progress</option>
                          <option value="submitted">Submitted</option>
                          <option value="accepted">Accepted 🎉</option>
                          <option value="rejected">Rejected</option>
                        </select>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

