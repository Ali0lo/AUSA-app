"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChatBox } from "@/components/ChatBox";

export default function ApplicationAssistantPage() {
  // Stateful tracker mirroring LangGraph state
  const [applicationStage, setApplicationStage] = useState<
    "gathering_info" | "drafting_documents" | "ready_to_submit"
  >("gathering_info");

  const [missingDocuments, setMissingDocuments] = useState<string[]>([
    "official_transcript",
    "passport_copy",
    "motivation_letter",
  ]);

  const stages = [
    { id: "gathering_info", label: "1. Gathering Info & Audit", desc: "Audit required dossier files" },
    { id: "drafting_documents", label: "2. Drafting Documents", desc: "Prepare motivation letter & SOP" },
    { id: "ready_to_submit", label: "3. Ready to Submit", desc: "Final verification before submission" },
  ];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200 mb-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Stateful LangGraph Workflow Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Application Preparation Assistant
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-2xl">
            Track your application stage, audit missing documents, verify official deadlines, and draft customized motivation letters with AI assistance.
          </p>
        </div>

        <Link
          href="/"
          className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-300 transition-all self-start md:self-auto"
        >
          ← Back to Matcher Dashboard
        </Link>
      </div>

      {/* Split-Screen Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Workflow Status Tracker (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Stage Progress Bar Card */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center justify-between">
              <span>Application Stage</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                {applicationStage}
              </span>
            </h3>

            {/* Step Indicators */}
            <div className="space-y-3 pt-1">
              {stages.map((st, idx) => {
                const isActive = applicationStage === st.id;
                return (
                  <div
                    key={st.id}
                    onClick={() => setApplicationStage(st.id as any)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer ${
                      isActive
                        ? "bg-blue-900 text-white border-blue-800 shadow-md"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold text-xs">
                      <span>{st.label}</span>
                      {isActive && <span className="text-emerald-400">Active</span>}
                    </div>
                    <p
                      className={`text-[11px] mt-0.5 ${
                        isActive ? "text-blue-200" : "text-slate-500"
                      }`}
                    >
                      {st.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Missing Documents Tracker Card */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>📋 Dossier Missing Documents</span>
              </h3>
              <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                {missingDocuments.length} Required
              </span>
            </div>

            <div className="space-y-2">
              {missingDocuments.map((doc, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-xl bg-amber-50/60 border border-amber-200 text-xs text-amber-900 font-medium"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-amber-600">⏳</span>
                    <span className="capitalize font-mono">
                      {doc.replace("_", " ")}
                    </span>
                  </div>
                  <button
                    onClick={() =>
                      setMissingDocuments(missingDocuments.filter((d) => d !== doc))
                    }
                    className="text-[10px] text-amber-700 hover:text-emerald-700 underline font-semibold"
                  >
                    Mark Ready ✓
                  </button>
                </div>
              ))}

              {missingDocuments.length === 0 && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs text-center font-medium">
                  🎉 All required dossier documents prepared!
                </div>
              )}
            </div>
          </div>

          {/* Target Program Info Card */}
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-sm space-y-2 border border-slate-800">
            <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400">
              Active Application Dossier
            </span>
            <h4 className="font-bold text-base text-white">
              MSc Computer Science
            </h4>
            <p className="text-xs text-slate-400">
              Technical University of Munich (TU Munich)
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex justify-between">
              <span>Deadline:</span>
              <span className="font-semibold text-white">Nov 30, 2026</span>
            </div>
          </div>
        </div>

        {/* Right Column: AI Assistant (8 Cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🤖 Interactive AI Assistant Drawer</span>
            </h2>
            <span className="text-xs text-slate-500">
              Select mode inside ChatBox to switch RAG vs LangGraph Agent
            </span>
          </div>

          {/* Embedded ChatBox */}
          <ChatBox studentId="std_demo" programId="prog_101" />
        </div>
      </div>
    </div>
  );
}
