"use client";

import { Plus, RefreshCw } from "lucide-react";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { ApplicationTracker } from "@/components/ApplicationTracker";
import { FeatureTag } from "@/components/FeatureTag";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { createTrackedApplication, fetchMyApplications, getUserFacingError, UserFacingError } from "@/lib/api";
import { TrackedApplication } from "@/types";

export default function ApplicationsTrackerPage() {
  const { data: session } = useSession();
  const [applications, setApplications] = useState<TrackedApplication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<UserFacingError | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newUniv, setNewUniv] = useState("");
  const [newProg, setNewProg] = useState("");
  const [newCountry, setNewCountry] = useState("Germany");
  const [newDeadline, setNewDeadline] = useState("2026-07-15");
  const [isAdding, setIsAdding] = useState(false);
  const token = session?.user?.accessToken;

  async function loadTracker() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchMyApplications("std_demo", token);
      setApplications(data);
    } catch (err) {
      setError(getUserFacingError(err, "Application tracker loading"));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTracker();
  }, [token]);

  async function handleAddProgram(e: React.FormEvent) {
    e.preventDefault();
    if (!newUniv.trim() || !newProg.trim()) return;
    setIsAdding(true);
    try {
      const created = await createTrackedApplication(
        {
          university_name: newUniv.trim(),
          program_name: newProg.trim(),
          country: newCountry,
          deadline: newDeadline,
          stage: "shortlisted",
          student_id: "std_demo"
        },
        token
      );
      setApplications((current) => [created, ...current]);
      setNewUniv("");
      setNewProg("");
      setShowAddForm(false);
    } catch (err) {
      setError(getUserFacingError(err, "Program tracker creation"));
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Application Lifecycle Management</p>
            <FeatureTag state="available" label="Live Tracker" />
          </div>
          <h1 className="page-heading mt-4">My Application Tracker & Deadlines</h1>
          <p className="body-large mt-5">
            Monitor target degree applications across stages and track approaching enrollment deadlines.
          </p>
        </div>
        <ServiceStatus />
      </div>

      <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
        <Notice title="Deadline Countdown Active" tone="info">
          Applications with deadlines under 14 days are automatically highlighted with an urgent red badge.
        </Notice>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="button-quiet" onClick={() => void loadTracker()} disabled={isLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            {isLoading ? "Refreshing..." : "Refresh Deadlines"}
          </button>
          <button type="button" className="button-primary" onClick={() => setShowAddForm((v) => !v)}>
            <Plus size={16} aria-hidden="true" />
            {showAddForm ? "Close Form" : "Add Program to Tracker"}
          </button>
        </div>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddProgram} className="mt-6 panel-strong p-6 bg-[#fbf9f4] border border-accent/40 space-y-4 max-w-2xl">
          <h3 className="font-serif text-xl font-semibold">Track New Program Application</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="field-label">University Name</label>
              <input
                type="text"
                className="field"
                required
                value={newUniv}
                onChange={(e) => setNewUniv(e.target.value)}
                placeholder="e.g. ADA University"
              />
            </div>
            <div>
              <label className="field-label">Program Name</label>
              <input
                type="text"
                className="field"
                required
                value={newProg}
                onChange={(e) => setNewProg(e.target.value)}
                placeholder="e.g. B.Sc. Computer Science"
              />
            </div>
            <div>
              <label className="field-label">Country</label>
              <input
                type="text"
                className="field"
                value={newCountry}
                onChange={(e) => setNewCountry(e.target.value)}
                placeholder="Germany / Azerbaijan"
              />
            </div>
            <div>
              <label className="field-label">Deadline (YYYY-MM-DD)</label>
              <input
                type="date"
                className="field"
                value={newDeadline}
                onChange={(e) => setNewDeadline(e.target.value)}
              />
            </div>
          </div>
          <button type="submit" className="button-primary" disabled={isAdding}>
            {isAdding ? "Adding..." : "Save to Tracker"}
          </button>
        </form>
      )}

      {error && (
        <div className="mt-6">
          <Notice title={error.title} tone="error" live>
            {error.message}
          </Notice>
        </div>
      )}

      <div className="mt-8">
        <ApplicationTracker initialApplications={applications} token={token} onRefresh={() => void loadTracker()} />
      </div>
    </div>
  );
}

