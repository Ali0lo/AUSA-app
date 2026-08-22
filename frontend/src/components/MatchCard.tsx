"use client";

import React from "react";
import { FactorScoreDetail, MatchResult } from "@/types";

interface MatchCardProps {
  result: MatchResult;
  onReset?: () => void;
}

export const MatchCard: React.FC<MatchCardProps> = ({ result, onReset }) => {
  const getScoreColorClass = (score: number) => {
    if (score >= 80) return "bg-emerald-500 text-emerald-400 border-emerald-500/30";
    if (score >= 50) return "bg-amber-500 text-amber-400 border-amber-500/30";
    return "bg-rose-500 text-rose-400 border-rose-500/30";
  };

  const getScoreBadgeClass = (score: number) => {
    if (score >= 80) return "bg-emerald-950/80 text-emerald-300 border border-emerald-500/40";
    if (score >= 50) return "bg-amber-950/80 text-amber-300 border border-amber-500/40";
    return "bg-rose-950/80 text-rose-300 border border-rose-500/40";
  };

  const renderFactorRow = (
    title: string,
    detail: FactorScoreDetail,
    weightLabel: string
  ) => {
    const isPassed = detail.passed_hard_filter;
    const progressColor = getScoreColorClass(detail.score).split(" ")[0];

    return (
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm space-y-2 transition-all hover:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-100 text-sm">{title}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              {weightLabel}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-md ${getScoreBadgeClass(detail.score)}`}>
              {detail.score.toFixed(1)}% Score
            </span>
            <span className="text-xs text-slate-400 font-mono">
              +{detail.weighted_score.toFixed(1)}% total
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
          <div
            className={`h-full ${progressColor} transition-all duration-500 ease-out`}
            style={{ width: `${Math.max(0, Math.min(100, detail.score))}%` }}
          />
        </div>

        {/* Explanation text */}
        <p className="text-xs text-slate-400 leading-relaxed pt-1">
          {detail.explanation}
        </p>
      </div>
    );
  };

  return (
    <div className="w-full rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-6 text-slate-100 backdrop-blur-md">
      {/* Header & Overall Match Gauge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest font-semibold text-blue-400">
            Matching Analysis Result
          </span>
          <h2 className="text-2xl font-bold text-white mt-1">
            {result.program_name}
          </h2>
          <p className="text-sm text-slate-400">{result.university_name}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Overall Compatibility
            </div>
            <div className="flex items-center justify-end gap-2 mt-1">
              <span className="text-4xl font-extrabold text-white tracking-tight">
                {result.overall_match_percentage.toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Eligibility Badge */}
          <div
            className={`px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 border shadow-lg ${
              result.is_eligible
                ? "bg-emerald-950/90 text-emerald-300 border-emerald-500/50 shadow-emerald-950/50"
                : "bg-rose-950/90 text-rose-300 border-rose-500/50 shadow-rose-950/50"
            }`}
          >
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                result.is_eligible ? "bg-emerald-400 animate-pulse" : "bg-rose-400"
              }`}
            />
            {result.is_eligible ? "Eligible Target" : "Ineligible / Rejection"}
          </div>
        </div>
      </div>

      {/* Ineligibility Reasons Warning Box */}
      {!result.is_eligible && result.ineligibility_reasons.length > 0 && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800/80 text-rose-200 text-xs space-y-1.5">
          <div className="font-bold flex items-center gap-2 text-rose-300 text-sm">
            <span>⚠️ Ineligibility Factors Detected:</span>
          </div>
          <ul className="list-disc list-inside space-y-1 pl-1">
            {result.ineligibility_reasons.map((reason, idx) => (
              <li key={idx} className="leading-normal">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Factor Score Breakdown Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Score Component Breakdown</span>
          <span className="text-xs font-normal text-slate-500">
            Deterministic Weights Enforced
          </span>
        </h3>

        <div className="grid grid-cols-1 gap-3">
          {renderFactorRow(
            "Academic Performance (GPA)",
            result.breakdown.academic,
            "Weight: 50%"
          )}
          {renderFactorRow(
            "Financial Budget Feasibility",
            result.breakdown.budget,
            "Weight: 30%"
          )}
          {renderFactorRow(
            "English Language Score",
            result.breakdown.language,
            "Weight: 20%"
          )}
          {renderFactorRow(
            "Degree Level Match",
            result.breakdown.degree_level,
            "Prerequisite Hard Filter"
          )}
        </div>
      </div>

      {onReset && (
        <div className="pt-2 flex justify-end">
          <button
            onClick={onReset}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-all border border-slate-700"
          >
            ← Test Another Program
          </button>
        </div>
      )}
    </div>
  );
};
