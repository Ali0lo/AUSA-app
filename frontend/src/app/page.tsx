"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { MatchCard } from "@/components/MatchCard";
import { fetchMatchScore } from "@/lib/api";
import {
  MatchResult,
  ProgramRequirements,
  StudentProfile,
} from "@/types";

// Mock Student Profile State
const MOCK_STUDENT: StudentProfile = {
  gpa: 3.6,
  budget: 18000,
  ielts: 7.0,
  toefl: 98,
  degree_level: "master",
  field_of_study: "Computer Science",
  preferred_countries: ["Germany", "Netherlands", "United Kingdom"],
};

// Hardcoded Mock University Programs for Discovery Column
const MOCK_PROGRAMS: ProgramRequirements[] = [
  {
    program_id: 101,
    university_name: "Technical University of Munich (TU Munich)",
    program_name: "MSc Computer Science",
    degree_level: "master",
    field: "Computer Science",
    country: "Germany",
    min_gpa: 3.2,
    tuition_fee: 12000,
    currency: "EUR",
    min_ielts: 6.5,
    min_toefl: 88,
  },
  {
    program_id: 102,
    university_name: "University College London (UCL)",
    program_name: "BSc Data Science",
    degree_level: "bachelor",
    field: "Data Science",
    country: "United Kingdom",
    min_gpa: 3.5,
    tuition_fee: 25000,
    currency: "GBP",
    min_ielts: 7.0,
    min_toefl: 100,
  },
  {
    program_id: 103,
    university_name: "University of Amsterdam (UvA)",
    program_name: "MSc Artificial Intelligence",
    degree_level: "master",
    field: "Artificial Intelligence",
    country: "Netherlands",
    min_gpa: 3.3,
    tuition_fee: 15000,
    currency: "EUR",
    min_ielts: 6.5,
    min_toefl: 92,
  },
];

export default function Dashboard() {
  const [selectedProgram, setSelectedProgram] = useState<ProgramRequirements>(
    MOCK_PROGRAMS[0]
  );
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const evaluateProgram = async (program: ProgramRequirements) => {
    setSelectedProgram(program);
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchMatchScore(MOCK_STUDENT, program);
      setMatchResult(result);
    } catch (err: any) {
      setError(
        err.message || "Unable to reach backend API at http://localhost:8000/api/v1"
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    evaluateProgram(MOCK_PROGRAMS[0]);
  }, []);

  return (
    <div className="space-y-8">
      {/* SaaS Dashboard Banner */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-800 text-xs font-semibold border border-blue-200 mb-2">
            <span>✨ Deterministic Matching Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Program Discovery & Compatibility Analysis
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-2xl">
            Select a target university program to run pure mathematical matching (Academics: 50%, Budget: 30%, Language: 20%) with zero LLM hallucinations.
          </p>
        </div>

        {/* Student Profile Quick Summary Card */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-1 text-slate-700 min-w-[240px]">
          <div className="font-bold text-slate-900 border-b border-slate-200 pb-1 flex justify-between">
            <span>Student Profile</span>
            <span className="text-blue-600 font-mono">GPA {MOCK_STUDENT.gpa}</span>
          </div>
          <div className="flex justify-between">
            <span>Budget:</span>
            <span className="font-semibold">${MOCK_STUDENT.budget.toLocaleString()}/yr</span>
          </div>
          <div className="flex justify-between">
            <span>IELTS / TOEFL:</span>
            <span className="font-semibold">{MOCK_STUDENT.ielts} / {MOCK_STUDENT.toefl}</span>
          </div>
          <div className="flex justify-between">
            <span>Target Level:</span>
            <span className="font-semibold uppercase text-blue-700">{MOCK_STUDENT.degree_level}</span>
          </div>
        </div>
      </div>

      {/* Split-Screen Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Discovery (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">
              Target Programs Discovery
            </h2>
            <span className="text-xs text-slate-500 font-medium">
              {MOCK_PROGRAMS.length} Available Programs
            </span>
          </div>

          <div className="space-y-3">
            {MOCK_PROGRAMS.map((program) => {
              const isSelected =
                selectedProgram.program_id === program.program_id;

              return (
                <div
                  key={program.program_id}
                  onClick={() => evaluateProgram(program)}
                  className={`p-5 rounded-2xl cursor-pointer transition-all duration-200 border text-left ${
                    isSelected
                      ? "bg-blue-900 text-white border-blue-800 shadow-lg shadow-blue-900/20 ring-2 ring-blue-600"
                      : "bg-white text-slate-900 border-gray-200 hover:border-blue-300 hover:shadow-md"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md ${
                          isSelected
                            ? "bg-blue-800 text-blue-200"
                            : "bg-slate-100 text-slate-600 border border-slate-200"
                        }`}
                      >
                        {program.degree_level} • {program.country}
                      </span>
                      <h3
                        className={`text-base font-bold mt-1.5 ${
                          isSelected ? "text-white" : "text-slate-900"
                        }`}
                      >
                        {program.program_name}
                      </h3>
                      <p
                        className={`text-xs ${
                          isSelected ? "text-blue-200" : "text-slate-500"
                        }`}
                      >
                        {program.university_name}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <div
                        className={`text-sm font-extrabold ${
                          isSelected ? "text-blue-200" : "text-slate-900"
                        }`}
                      >
                        {program.currency} {program.tuition_fee.toLocaleString()}
                      </div>
                      <div
                        className={`text-[10px] ${
                          isSelected ? "text-blue-300" : "text-slate-400"
                        }`}
                      >
                        / academic year
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-700/40 flex items-center justify-between text-xs">
                    <span className={isSelected ? "text-blue-200" : "text-slate-500"}>
                      Min GPA: <strong className={isSelected ? "text-white" : "text-slate-800"}>{program.min_gpa}</strong>
                    </span>
                    <span className={isSelected ? "text-blue-200" : "text-slate-500"}>
                      IELTS: <strong className={isSelected ? "text-white" : "text-slate-800"}>{program.min_ielts}</strong>
                    </span>
                    <span
                      className={`font-semibold ${
                        isSelected ? "text-white" : "text-blue-600"
                      }`}
                    >
                      {isSelected ? "Selected ✓" : "Analyze Match →"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Analysis & MatchCard (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">
              Deterministic Compatibility Analysis
            </h2>
            {isLoading && (
              <span className="text-xs font-semibold text-blue-600 animate-pulse">
                Evaluating math model...
              </span>
            )}
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              <strong>Error:</strong> {error}
            </div>
          )}

          {matchResult ? (
            <div className="space-y-6">
              <MatchCard result={matchResult} />

              {/* Start Application Route Button */}
              <div className="p-6 bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-bold text-slate-900 text-base">
                    Ready to Prepare Your Application?
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Transition to the Application Assistant to track missing documents, verify deadlines, and draft your motivation letter.
                  </p>
                </div>

                <Link
                  href="/application"
                  className="px-6 py-3 rounded-xl bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm transition-all shadow-lg shadow-blue-900/20 text-center shrink-0 flex items-center justify-center gap-2"
                >
                  <span>Start Application</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center text-slate-500">
              Select a program on the left to view detailed match breakdown.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
