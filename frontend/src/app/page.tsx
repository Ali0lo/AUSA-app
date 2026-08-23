"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { signIn, useSession } from "next-auth/react";
import { MatchCard } from "@/components/MatchCard";
import { fetchCurrentStudentProfile, fetchMatchScore } from "@/lib/api";
import {
  MatchResult,
  ProgramRequirements,
  StudentProfile,
} from "@/types";

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
  const { data: session, status } = useSession();

  // Login Form State
  const [loginEmail, setLoginEmail] = useState("student@ausa.az");
  const [loginPassword, setLoginPassword] = useState("password123");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Authenticated Student State
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<ProgramRequirements>(MOCK_PROGRAMS[0]);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Load student profile when authenticated session is active
  useEffect(() => {
    if (session && (session.user as any)?.accessToken) {
      const token = (session.user as any).accessToken;
      
      // If profile is in session, use it immediately
      if ((session.user as any)?.profile) {
        setStudentProfile((session.user as any).profile);
      }

      // Fetch fresh profile from API
      fetchCurrentStudentProfile(token)
        .then((profile) => {
          setStudentProfile(profile);
          evaluateMatchForStudent(profile, MOCK_PROGRAMS[0], token);
        })
        .catch(() => {
          // Fallback to default student profile if offline
          const fallback: StudentProfile = {
            gpa: 3.6,
            budget: 18000,
            ielts: 7.0,
            toefl: 98,
            degree_level: "master",
            field_of_study: "Computer Science",
          };
          setStudentProfile(fallback);
          evaluateMatchForStudent(fallback, MOCK_PROGRAMS[0], token);
        });
    }
  }, [session]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError(null);

    const result = await signIn("credentials", {
      email: loginEmail,
      password: loginPassword,
      redirect: false,
    });

    setIsLoggingIn(false);

    if (result?.error) {
      setLoginError("Invalid email or password. Please verify credentials.");
    }
  };

  const evaluateMatchForStudent = async (
    student: StudentProfile,
    program: ProgramRequirements,
    token?: string
  ) => {
    setSelectedProgram(program);
    setIsEvaluating(true);
    setEvalError(null);

    try {
      const result = await fetchMatchScore(student, program, token);
      setMatchResult(result);
    } catch (err: any) {
      setEvalError(
        err.message || "Failed to evaluate program match."
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  // 1. Loading State
  if (status === "loading") {
    return (
      <div className="min-h-[400px] flex items-center justify-center text-slate-500 font-medium text-sm">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Verifying authentication session...</span>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated State (Clean Login Form)
  if (!session) {
    return (
      <div className="max-w-md mx-auto my-12 bg-white border border-gray-200 rounded-2xl p-8 shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-blue-900 text-white font-bold text-xl flex items-center justify-center mx-auto shadow-md">
            A
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Sign In to AUSA Platform
          </h2>
          <p className="text-xs text-slate-500">
            Access your personalized student profile and deterministic program matching engine.
          </p>
        </div>

        <form onSubmit={handleLoginSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-300 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 transition-colors"
              placeholder="student@ausa.edu.az"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-300 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 transition-colors"
            />
          </div>

          {loginError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {loginError}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full py-3 rounded-xl bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm transition-all shadow-md shadow-blue-900/20 disabled:opacity-50"
          >
            {isLoggingIn ? "Authenticating..." : "Sign In to Dashboard"}
          </button>
        </form>

        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500 text-center space-y-0.5">
          <div className="font-semibold text-slate-700">🔑 Default Demo Credentials:</div>
          <div>Email: <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">student@ausa.az</code></div>
          <div>Password: <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">password123</code></div>
        </div>
      </div>
    );
  }

  // 3. Authenticated State (Dashboard View with Logged-In Student Profile)
  const token = (session.user as any)?.accessToken;

  return (
    <div className="space-y-8">
      {/* SaaS Dashboard Banner */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-800 text-xs font-semibold border border-blue-200 mb-2">
            <span>🔒 Authenticated Session Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Program Discovery & Compatibility Analysis
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-2xl">
            Welcome back, <strong>{session.user?.email}</strong>. Evaluating program options against your database profile.
          </p>
        </div>

        {/* Dynamic Logged-In Student Profile Summary Card */}
        {studentProfile && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-1 text-slate-700 min-w-[260px] shadow-sm">
            <div className="font-bold text-slate-900 border-b border-slate-200 pb-1 flex justify-between">
              <span>Your Database Profile</span>
              <span className="text-blue-700 font-mono font-bold">GPA {studentProfile.gpa}</span>
            </div>
            <div className="flex justify-between">
              <span>Annual Budget:</span>
              <span className="font-semibold">${studentProfile.budget.toLocaleString()}/yr</span>
            </div>
            <div className="flex justify-between">
              <span>IELTS / TOEFL:</span>
              <span className="font-semibold">{studentProfile.ielts || "N/A"} / {studentProfile.toefl || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span>Degree Level:</span>
              <span className="font-semibold uppercase text-blue-700">{studentProfile.degree_level}</span>
            </div>
          </div>
        )}
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
              {MOCK_PROGRAMS.length} Programs Available
            </span>
          </div>

          <div className="space-y-3">
            {MOCK_PROGRAMS.map((program) => {
              const isSelected =
                selectedProgram.program_id === program.program_id;

              return (
                <div
                  key={program.program_id}
                  onClick={() => {
                    if (studentProfile) {
                      evaluateMatchForStudent(studentProfile, program, token);
                    }
                  }}
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
            {isEvaluating && (
              <span className="text-xs font-semibold text-blue-600 animate-pulse">
                Evaluating match...
              </span>
            )}
          </div>

          {evalError && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              <strong>Error:</strong> {evalError}
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
