"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { ApplicationStage, ApplicationStepper } from "@/components/ApplicationStepper";
import { ChatBox } from "@/components/ChatBox";
import { DocumentChecklist } from "@/components/DocumentChecklist";
import { fetchAgentState } from "@/lib/api";

export default function ApplicationAssistantPage() {
  const { data: session } = useSession();
  const token = (session?.user as any)?.accessToken;

  // Agent State
  const [applicationStage, setApplicationStage] =
    useState<ApplicationStage>("gathering_info");
  const [missingDocuments, setMissingDocuments] = useState<string[]>([
    "official_transcript",
    "passport_copy",
    "motivation_letter",
  ]);
  const [draftedLetter, setDraftedLetter] = useState<string | null>(null);
  const [isLoadingState, setIsLoadingState] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  // Fetch initial Agent state on mount
  useEffect(() => {
    fetchAgentState("std_demo", "prog_101", token)
      .then((data) => {
        if (data.application_stage) {
          setApplicationStage(data.application_stage as ApplicationStage);
        }
        if (data.missing_documents) {
          setMissingDocuments(data.missing_documents);
        }
        if (data.drafted_motivation_letter) {
          setDraftedLetter(data.drafted_motivation_letter);
        }
      })
      .catch(() => {
        // Fallback default state if offline
      })
      .finally(() => {
        setIsLoadingState(false);
      });
  }, [token]);

  // Callback triggered when Agent executes a tool call in ChatBox
  const handleAgentStateUpdate = (
    stage: string,
    docs: string[],
    newLetter?: string
  ) => {
    if (stage) {
      setApplicationStage(stage as ApplicationStage);
    }
    if (docs) {
      setMissingDocuments(docs);
    }
    if (newLetter) {
      setDraftedLetter(newLetter);
    }
  };

  const handleToggleDocument = (docName: string) => {
    const updated = missingDocuments.filter((d) => d !== docName);
    setMissingDocuments(updated);
    if (updated.length === 0) {
      setApplicationStage("ready_to_submit");
    }
  };

  const handleCopyLetter = () => {
    if (draftedLetter) {
      navigator.clipboard.writeText(draftedLetter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-800 text-xs font-semibold border border-blue-200 mb-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Stateful LangGraph Workflow Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Application Preparation Assistant
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-2xl">
            Track your application stage, audit missing documents, and converse with the LangGraph AI Agent to draft your motivation letter.
          </p>
        </div>

        <Link
          href="/"
          className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-300 transition-all self-start md:self-auto"
        >
          ← Back to Matcher Dashboard
        </Link>
      </div>

      {/* Two-Column Dashboard Layout (60% Left / 40% Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (60% Width -> 7 cols on lg grid) */}
        <div className="lg:col-span-7 space-y-6">
          {/* 1. Progress Stepper Component */}
          <ApplicationStepper currentStage={applicationStage} />

          {/* 2. Missing Documents Checklist Component */}
          <DocumentChecklist
            missingDocuments={missingDocuments}
            onToggleDocument={handleToggleDocument}
          />

          {/* 3. Generated Documents Section (Drafted Motivation Letter) */}
          <div className="w-full bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                  <span>✉️ Generated Documents</span>
                </h3>
                <p className="text-xs text-slate-500">
                  Customized application materials drafted by the LangGraph agent
                </p>
              </div>

              {draftedLetter && (
                <button
                  onClick={handleCopyLetter}
                  className="px-3 py-1.5 rounded-lg bg-blue-900 hover:bg-blue-800 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
                >
                  <span>{copied ? "Copied! ✓" : "Copy Draft"}</span>
                </button>
              )}
            </div>

            {draftedLetter ? (
              <div className="bg-slate-900 text-slate-100 p-5 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-xs text-slate-400">
                  <span className="font-mono font-bold text-blue-400">
                    Drafted Motivation Letter
                  </span>
                  <span>Target: TU Munich (prog_101)</span>
                </div>
                <div className="font-mono text-xs leading-relaxed whitespace-pre-wrap text-slate-200">
                  {draftedLetter}
                </div>
              </div>
            ) : (
              <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2 text-slate-500">
                <div className="text-xl">📝</div>
                <div className="font-bold text-slate-800 text-sm">
                  No Generated Motivation Letter Yet
                </div>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Ask the LangGraph Agent in the right column (e.g. <em>"Draft my motivation letter"</em>) to automatically generate a customized statement of purpose.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (40% Width -> 5 cols on lg grid) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <h2 className="text-sm font-bold text-slate-900">
                Application Guide Chat Assistant
              </h2>
            </div>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">
              Agent Locked
            </span>
          </div>

          {/* Embedded ChatBox locked into Agent Mode */}
          <ChatBox
            studentId="std_demo"
            programId="prog_101"
            lockedMode="agent"
            token={token}
            onStateUpdate={handleAgentStateUpdate}
          />
        </div>
      </div>
    </div>
  );
}
