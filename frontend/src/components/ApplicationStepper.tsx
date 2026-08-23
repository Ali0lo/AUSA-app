"use client";

import React from "react";

export type ApplicationStage = "gathering_info" | "drafting_documents" | "ready_to_submit";

interface ApplicationStepperProps {
  currentStage: ApplicationStage | string;
}

interface StepItem {
  id: ApplicationStage;
  number: number;
  label: string;
  description: string;
}

const STEPS: StepItem[] = [
  {
    id: "gathering_info",
    number: 1,
    label: "Gathering Info",
    description: "Audit required dossier files",
  },
  {
    id: "drafting_documents",
    number: 2,
    label: "Drafting Documents",
    description: "Prepare motivation letter & SOP",
  },
  {
    id: "ready_to_submit",
    number: 3,
    label: "Ready to Submit",
    description: "Final dossier verification",
  },
];

export const ApplicationStepper: React.FC<ApplicationStepperProps> = ({
  currentStage,
}) => {
  const getStepStatus = (stepId: ApplicationStage, index: number) => {
    const stageOrder: Record<string, number> = {
      gathering_info: 0,
      drafting_documents: 1,
      ready_to_submit: 2,
    };

    const currentOrder = stageOrder[currentStage] ?? 0;

    if (index < currentOrder) return "completed";
    if (index === currentOrder) return "active";
    return "upcoming";
  };

  return (
    <div className="w-full bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div>
          <h3 className="font-extrabold text-slate-900 text-base">
            LangGraph Application Progress Tracker
          </h3>
          <p className="text-xs text-slate-500">
            Stateful multi-step dossier preparation workflow
          </p>
        </div>

        <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-blue-50 text-blue-900 border border-blue-200">
          Stage: {currentStage}
        </span>
      </div>

      {/* Horizontal Timeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {STEPS.map((step, idx) => {
          const status = getStepStatus(step.id, idx);
          const isCompleted = status === "completed";
          const isActive = status === "active";

          return (
            <div
              key={step.id}
              className={`relative p-4 rounded-xl border transition-all ${
                isActive
                  ? "bg-blue-900 text-white border-blue-800 shadow-md ring-2 ring-blue-600"
                  : isCompleted
                  ? "bg-blue-950 text-blue-100 border-blue-900"
                  : "bg-slate-50 text-slate-600 border-slate-200"
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Step Circle Badge */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                    isActive
                      ? "bg-blue-600 text-white shadow-inner"
                      : isCompleted
                      ? "bg-emerald-500 text-white"
                      : "bg-slate-200 text-slate-600"
                  }`}
                >
                  {isCompleted ? "✓" : step.number}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="font-bold text-sm leading-tight flex items-center justify-between">
                    <span className="truncate">{step.label}</span>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                    )}
                  </div>
                  <p
                    className={`text-[11px] mt-0.5 truncate ${
                      isActive
                        ? "text-blue-200"
                        : isCompleted
                        ? "text-blue-300"
                        : "text-slate-500"
                    }`}
                  >
                    {step.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
