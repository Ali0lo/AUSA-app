"use client";

import { Clipboard, RefreshCw } from "lucide-react";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { ApplicationStage, ApplicationStepper } from "@/components/ApplicationStepper";
import { ChatBox } from "@/components/ChatBox";
import { DocumentChecklist } from "@/components/DocumentChecklist";
import { FeatureTag } from "@/components/FeatureTag";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { fetchAgentState, getUserFacingError, UserFacingError } from "@/lib/api";

const initialDocuments = ["official_transcript", "passport_copy", "motivation_letter"];

export default function ApplicationPage() {
  const { data: session } = useSession();
  const [stage, setStage] = useState<ApplicationStage>("gathering_info");
  const [missingDocuments, setMissingDocuments] = useState<string[]>(initialDocuments);
  const [draftedLetter, setDraftedLetter] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<UserFacingError | null>(null);
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">("idle");
  const token = session?.user?.accessToken;

  async function loadState() {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await fetchAgentState("std_demo", "prog_101", token);
      setStage((data.application_stage || "gathering_info") as ApplicationStage);
      setMissingDocuments(data.missing_documents || []);
      setDraftedLetter(data.drafted_motivation_letter || null);
    } catch (error) {
      setLoadError(getUserFacingError(error, "Application-state loading"));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    fetchAgentState("std_demo", "prog_101", token)
      .then((data) => {
        if (!active) return;
        setStage((data.application_stage || "gathering_info") as ApplicationStage);
        setMissingDocuments(data.missing_documents || []);
        setDraftedLetter(data.drafted_motivation_letter || null);
        setLoadError(null);
      })
      .catch((error) => {
        if (active) setLoadError(getUserFacingError(error, "Application-state loading"));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  function toggleDocument(document: string) {
    setMissingDocuments((current) => {
      const next = current.includes(document)
        ? current.filter((item) => item !== document)
        : [...current, document];
      setStage(next.length === 0 ? "ready_to_submit" : draftedLetter ? "drafting_documents" : "gathering_info");
      return next;
    });
  }

  function resetDemo() {
    setMissingDocuments(initialDocuments);
    setStage("gathering_info");
    setDraftedLetter(null);
    setLoadError(null);
    setCopyStatus("idle");
  }

  async function copyLetter() {
    if (!draftedLetter) return;
    try {
      await navigator.clipboard.writeText(draftedLetter);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Application preparation</p>
            <FeatureTag state="demo" label="Demo workflow" />
          </div>
          <h1 className="page-heading mt-4">Exercise the current application-assistant workflow.</h1>
          <p className="body-large mt-5">
            This page connects to the existing LangGraph endpoints while identifying the canned document, deadline, and letter data as a demonstration.
          </p>
        </div>
        <ServiceStatus />
      </div>

      <div className="mt-7 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
        <Notice title="Local demonstration state" tone="warning">
          Checklist changes are not saved. The agent tools currently return mock values, and this frontend does not submit applications.
        </Notice>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="button-quiet" onClick={() => void loadState()} disabled={isLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            {isLoading ? "Loading state" : "Reload backend state"}
          </button>
          <button type="button" className="button-secondary" onClick={resetDemo}>Reset local demo</button>
        </div>
      </div>

      {loadError && (
        <div className="mt-6">
          <Notice title={loadError.title} tone="error" live>
            {loadError.message} The local checklist and chat interface remain available.
          </Notice>
        </div>
      )}

      <div className="mt-9 space-y-7">
        <ApplicationStepper currentStage={stage} />
        <div className="grid gap-7 xl:grid-cols-[1fr_0.95fr] xl:items-start">
          <div className="space-y-7">
            <DocumentChecklist missingDocuments={missingDocuments} onToggleDocument={toggleDocument} />

            <section className="panel-strong p-6 sm:p-8" aria-labelledby="generated-document-heading">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
                <div>
                  <h2 id="generated-document-heading" className="font-serif text-2xl font-semibold">Motivation-letter draft</h2>
                  <p className="mt-1 text-sm text-muted">Returned by the current demonstration tool for student <code className="font-mono text-xs">std_demo</code> and programme <code className="font-mono text-xs">prog_101</code>.</p>
                </div>
                {draftedLetter && (
                  <button type="button" className="button-quiet" onClick={() => void copyLetter()}>
                    <Clipboard size={16} aria-hidden="true" />
                    Copy draft
                  </button>
                )}
              </div>

              {copyStatus === "copied" && <p className="mt-4 text-sm font-semibold text-success" role="status">Draft copied to the clipboard.</p>}
              {copyStatus === "failed" && <p className="mt-4 text-sm font-semibold text-danger" role="alert">Clipboard access failed. Select the draft manually and copy it.</p>}

              {draftedLetter ? (
                <pre className="mt-6 overflow-x-auto whitespace-pre-wrap border border-quiet bg-[#f8f5ef] p-5 font-sans text-sm leading-7 text-ink">{draftedLetter}</pre>
              ) : (
                <div className="mt-6 border border-quiet bg-[#f8f5ef] p-6">
                  <p className="font-semibold">No draft is currently loaded.</p>
                  <p className="mt-2 text-sm leading-6 text-muted">Ask the application assistant to draft a motivation letter. If the backend returns one, it will appear here.</p>
                </div>
              )}
            </section>
          </div>

          <ChatBox
            studentId="std_demo"
            programId="prog_101"
            lockedMode="agent"
            token={session?.user?.accessToken}
            onStateUpdate={(nextStage, documents, letter) => {
              setStage(nextStage as ApplicationStage);
              setMissingDocuments(documents);
              if (letter) setDraftedLetter(letter);
            }}
          />
        </div>
      </div>
    </div>
  );
}
