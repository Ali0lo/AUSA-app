"use client";

import React, { useState, useMemo } from "react";
import {
  ScholarshipBrief,
  ScholarshipDetail,
  ScholarshipStatus,
  EvaluationItemResponse,
  FALLBACK_SCHOLARSHIPS,
  evaluateScholarshipsLocal,
} from "@/lib/scholarships-api";
import {
  GraduationCap,
  Award,
  Search,
  CheckCircle2,
  AlertCircle,
  XCircle,
  HelpCircle,
  Sliders,
  ExternalLink,
  Calendar,
  Globe,
  Coins,
  ShieldAlert,
  FileText,
  UserCheck,
  ChevronRight,
  X,
  Sparkles,
} from "lucide-react";

export function ScholarshipExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("all");
  const [selectedDegree, setSelectedDegree] = useState("all");
  const [selectedFunding, setSelectedFunding] = useState("all");

  // Evaluation drawer & state
  const [showEvaluator, setShowEvaluator] = useState(false);
  const [evalLevel, setEvalLevel] = useState("master");
  const [evalAge, setEvalAge] = useState<number | "">(24);
  const [evalGpa, setEvalGpa] = useState<number | "">(3.6);
  const [evalIelts, setEvalIelts] = useState<number | "">(7.0);
  const [evalHours, setEvalHours] = useState<number | "">(3000);
  const [evalEmployer, setEvalEmployer] = useState("");
  const [evalDimScore, setEvalDimScore] = useState<number | "">(660);
  const [evalIncomeAzn, setEvalIncomeAzn] = useState<number | "">(22000);

  // Active status filter tab for evaluated view ("all", "open", "unlockable", "blocked")
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Detailed modal scholarship
  const [modalScholarship, setModalScholarship] = useState<ScholarshipDetail | null>(null);

  // Run evaluation
  const evaluation = useMemo(() => {
    return evaluateScholarshipsLocal({
      level_sought: evalLevel,
      age: evalAge === "" ? null : Number(evalAge),
      gpa: evalGpa === "" ? null : Number(evalGpa),
      gpa_scale: "4.0",
      ielts: evalIelts === "" ? null : Number(evalIelts),
      work_experience_hours: evalHours === "" ? null : Number(evalHours),
      employer: evalEmployer.trim() || null,
      dim_score: evalDimScore === "" ? null : Number(evalDimScore),
      family_household_income_azn: evalIncomeAzn === "" ? null : Number(evalIncomeAzn),
      is_azerbaijani_citizen: true,
    });
  }, [evalLevel, evalAge, evalGpa, evalIelts, evalHours, evalEmployer, evalDimScore, evalIncomeAzn]);

  // Create evaluation map by key
  const evalMap = useMemo(() => {
    const map = new Map<string, EvaluationItemResponse>();
    for (const r of evaluation.results) {
      map.set(r.scholarship.key, r);
    }
    return map;
  }, [evaluation]);

  // Filtered scholarships
  const filteredScholarships = useMemo(() => {
    return FALLBACK_SCHOLARSHIPS.filter((s) => {
      // Evaluation status filter
      if (showEvaluator && statusFilter !== "all") {
        const ev = evalMap.get(s.key);
        if (!ev || ev.status !== statusFilter) {
          return false;
        }
      }

      // Country filter
      if (selectedCountry !== "all") {
        if (selectedCountry === "AZ" && s.country_code !== "AZ") return false;
        if (selectedCountry === "GB" && s.country_code !== "GB") return false;
        if (selectedCountry === "US" && s.country_code !== "US") return false;
        if (selectedCountry === "DE" && s.country_code !== "DE") return false;
        if (selectedCountry === "IT" && s.country_code !== "IT") return false;
        if (selectedCountry === "HU" && s.country_code !== "HU") return false;
        if (selectedCountry === "TR" && s.country_code !== "TR") return false;
        if (selectedCountry === "FR" && s.country_code !== "FR") return false;
        if (selectedCountry === "PL" && s.country_code !== "PL") return false;
        if (selectedCountry === "CN" && s.country_code !== "CN") return false;
      }

      // Degree filter
      if (selectedDegree !== "all" && !s.degree_levels.includes(selectedDegree)) {
        return false;
      }

      // Funding type filter
      if (selectedFunding !== "all" && s.funding_type !== selectedFunding) {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.native_name.toLowerCase().includes(q) ||
          s.provider.toLowerCase().includes(q) ||
          s.country_name.toLowerCase().includes(q) ||
          s.coverage_summary.toLowerCase().includes(q)
        );
      }

      return true;
    });
  }, [selectedCountry, selectedDegree, selectedFunding, searchQuery, showEvaluator, statusFilter, evalMap]);

  return (
    <div className="w-full space-y-8 animate-fade-in">
      {/* Hero Header Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.06] via-white/[0.02] to-transparent p-6 sm:p-8 backdrop-blur-2xl">
        <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-orange-400">
              <Award className="h-3.5 w-3.5" />
              Comprehensive Global Scholarship Engine
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Global & Bilateral Scholarships Hub
            </h1>
            <p className="max-w-2xl text-sm sm:text-base text-slate-300">
              Explore 14 official government, bilateral, and state scholarship programmes accessible to Azerbaijani students.
              Evaluate discrete qualification gates (Chevening work hours, YTB age limits, Italian ISEE-U ceilings) with honest feedback.
            </p>
          </div>

          <button
            onClick={() => setShowEvaluator(!showEvaluator)}
            className={`self-start md:self-center inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition-all shadow-lg active:scale-95 ${
              showEvaluator
                ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-orange-500/25 border border-orange-400"
                : "bg-white/[0.08] hover:bg-white/15 text-white border border-white/15"
            }`}
          >
            <Sparkles className="h-4 w-4 text-amber-300" />
            <span>{showEvaluator ? "Close Eligibility Checker" : "Assess My Eligibility"}</span>
          </button>
        </div>
      </div>

      {/* Interactive Eligibility Assessment Drawer */}
      {showEvaluator && (
        <div className="rounded-3xl border border-orange-500/30 bg-gradient-to-b from-orange-500/10 via-purple-500/5 to-slate-900/40 p-6 sm:p-8 backdrop-blur-2xl space-y-6 animate-slide-down shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Sliders className="h-5 w-5 text-orange-400" />
                Student Profile Eligibility Evaluator
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Discrete qualification assessment under ADR-0001 & ADR-0008 (No speculative percentages or weighted match scores).
              </p>
            </div>

            {/* Quick Status Pill Metrics */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setStatusFilter("open")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  statusFilter === "open"
                    ? "bg-emerald-500/30 text-emerald-200 border border-emerald-400"
                    : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20"
                }`}
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{evaluation.open_count} OPEN</span>
              </button>

              <button
                onClick={() => setStatusFilter("unlockable")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  statusFilter === "unlockable"
                    ? "bg-amber-500/30 text-amber-200 border border-amber-400"
                    : "bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20"
                }`}
              >
                <AlertCircle className="h-3.5 w-3.5" />
                <span>{evaluation.unlockable_count} UNLOCKABLE</span>
              </button>

              <button
                onClick={() => setStatusFilter("blocked")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  statusFilter === "blocked"
                    ? "bg-red-500/30 text-red-200 border border-red-400"
                    : "bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/20"
                }`}
              >
                <XCircle className="h-3.5 w-3.5" />
                <span>{evaluation.blocked_count} BLOCKED</span>
              </button>

              <button
                onClick={() => setStatusFilter("all")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  statusFilter === "all"
                    ? "bg-white/20 text-white border border-white/30"
                    : "bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
              >
                All (14)
              </button>
            </div>
          </div>

          {/* Input Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Degree Level Sought</label>
              <select
                value={evalLevel}
                onChange={(e) => setEvalLevel(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="bachelor" className="bg-slate-900 text-white">Bachelor&apos;s</option>
                <option value="master" className="bg-slate-900 text-white">Master&apos;s</option>
                <option value="phd" className="bg-slate-900 text-white">Doctoral / PhD</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Your Age (Years)</label>
              <input
                type="number"
                min="15"
                max="75"
                value={evalAge}
                onChange={(e) => setEvalAge(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 24"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">GPA (out of 4.0)</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="4.0"
                value={evalGpa}
                onChange={(e) => setEvalGpa(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 3.6"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">IELTS Academic Score</label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="9.0"
                value={evalIelts}
                onChange={(e) => setEvalIelts(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 7.0"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Work Experience (Hours)</label>
              <input
                type="number"
                step="100"
                min="0"
                value={evalHours}
                onChange={(e) => setEvalHours(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 3,000"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <span className="text-[10px] text-slate-400">Chevening requires 2,800 documented hours.</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Employer Organization</label>
              <input
                type="text"
                value={evalEmployer}
                onChange={(e) => setEvalEmployer(e.target.value)}
                placeholder="e.g. SOCAR, Ministry, Bank"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <span className="text-[10px] text-slate-400">Required for SOCAR Talent award.</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">DİM Entrance Exam Score</label>
              <input
                type="number"
                min="0"
                max="700"
                value={evalDimScore}
                onChange={(e) => setEvalDimScore(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 660"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <span className="text-[10px] text-slate-400">BHOS full scholarship requires 650+.</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Annual Household Income (AZN)</label>
              <input
                type="number"
                step="2000"
                min="0"
                value={evalIncomeAzn}
                onChange={(e) => setEvalIncomeAzn(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="e.g. 24,000"
                className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <span className="text-[10px] text-slate-400">Italian DSU ceiling is €25k (~46,000 AZN).</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by scholarship name, country, provider, or benefits..."
              className="w-full rounded-2xl border border-white/10 bg-[#0c0d1b]/90 pl-10 pr-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500 backdrop-blur-xl"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <select
              value={selectedDegree}
              onChange={(e) => setSelectedDegree(e.target.value)}
              className="rounded-2xl border border-white/10 bg-[#0c0d1b]/90 px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500 backdrop-blur-xl"
            >
              <option value="all" className="bg-slate-900 text-white">All Degree Levels</option>
              <option value="bachelor" className="bg-slate-900 text-white">Bachelor&apos;s</option>
              <option value="master" className="bg-slate-900 text-white">Master&apos;s</option>
              <option value="phd" className="bg-slate-900 text-white">PhD / Doctoral</option>
            </select>

            <select
              value={selectedFunding}
              onChange={(e) => setSelectedFunding(e.target.value)}
              className="rounded-2xl border border-white/10 bg-[#0c0d1b]/90 px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500 backdrop-blur-xl"
            >
              <option value="all" className="bg-slate-900 text-white">All Funding Tiers</option>
              <option value="fully_funded" className="bg-slate-900 text-white">100% Fully Funded</option>
              <option value="tuition_reduction" className="bg-slate-900 text-white">Tuition Reduction</option>
            </select>
          </div>
        </div>

        {/* Country Filter Chips */}
        <div className="flex flex-wrap gap-1.5 p-1 rounded-2xl border border-white/[0.06] bg-white/[0.02]">
          {[
            { id: "all", label: "All Destinations" },
            { id: "GB", label: "🇬🇧 UK" },
            { id: "US", label: "🇺🇸 USA" },
            { id: "DE", label: "🇩🇪 Germany" },
            { id: "IT", label: "🇮🇹 Italy" },
            { id: "HU", label: "🇭🇺 Hungary" },
            { id: "TR", label: "🇹🇷 Turkey" },
            { id: "FR", label: "🇫🇷 France" },
            { id: "PL", label: "🇵🇱 Poland" },
            { id: "CN", label: "🇨🇳 China" },
            { id: "AZ", label: "🇦🇿 Azerbaijan" },
          ].map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCountry(c.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                selectedCountry === c.id
                  ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-white/[0.05]"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Scholarships Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>Showing {filteredScholarships.length} of 14 scholarships</span>
          {showEvaluator && (
            <span className="text-orange-400 font-medium">
              Profile filter active ({statusFilter.toUpperCase()})
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredScholarships.map((sch) => {
            const ev = evalMap.get(sch.key);

            return (
              <div
                key={sch.key}
                className="group relative flex flex-col justify-between rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.05] via-white/[0.02] to-transparent p-6 backdrop-blur-xl transition-all duration-300 hover:border-white/20 hover:scale-[1.01] hover:shadow-2xl"
              >
                <div className="space-y-4">
                  {/* Top Bar: Funding Badge & Country */}
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider ${
                        sch.funding_type === "fully_funded"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {sch.funding_type === "fully_funded" ? "100% Fully Funded" : "Tuition Reduction"}
                    </span>

                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                      <Globe className="h-3.5 w-3.5 text-slate-400" />
                      {sch.country_name.split(" ")[0]}
                    </span>
                  </div>

                  {/* Qualification Status Pill (if Evaluator is open) */}
                  {showEvaluator && ev && (
                    <div
                      className={`flex items-center gap-2 rounded-xl p-2.5 text-xs font-medium ${
                        ev.status === "open"
                          ? "bg-emerald-500/15 text-emerald-200 border border-emerald-500/30"
                          : ev.status === "unlockable"
                          ? "bg-amber-500/15 text-amber-200 border border-amber-500/30"
                          : "bg-red-500/15 text-red-200 border border-red-500/30"
                      }`}
                    >
                      {ev.status === "open" && <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />}
                      {ev.status === "unlockable" && <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />}
                      {ev.status === "blocked" && <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />}
                      <span className="truncate">
                        <strong>{ev.status.toUpperCase()}</strong>: {ev.summary_verdict}
                      </span>
                    </div>
                  )}

                  {/* Title & Provider */}
                  <div>
                    <h3 className="text-lg font-bold text-white group-hover:text-orange-400 transition-colors">
                      {sch.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">{sch.provider}</p>
                  </div>

                  {/* Degree Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {sch.degree_levels.map((lvl) => (
                      <span
                        key={lvl}
                        className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] font-semibold text-slate-300 uppercase"
                      >
                        {lvl}
                      </span>
                    ))}
                  </div>

                  {/* Coverage Description */}
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {sch.coverage_summary}
                  </p>

                  {/* Highlights Bar: Stipend & Quota */}
                  <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 space-y-1.5 text-xs">
                    {sch.stipend_monthly_local && (
                      <div className="flex items-center justify-between text-slate-300">
                        <span className="text-slate-400">Monthly Stipend:</span>
                        <span className="font-semibold text-white">{sch.stipend_monthly_local}</span>
                      </div>
                    )}

                    {sch.azerbaijan_quota_or_seats && (
                      <div className="flex items-center justify-between text-slate-300">
                        <span className="text-slate-400">Azerbaijan Quota:</span>
                        <span className="font-medium text-amber-300 text-right text-[11px]">
                          {sch.azerbaijan_quota_or_seats.split(";")[0].slice(0, 32)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Critical Obligation Notice */}
                  {sch.return_service_obligation && (
                    <div className="flex items-start gap-1.5 rounded-xl border border-amber-500/20 bg-amber-500/5 p-2.5 text-[11px] text-amber-200">
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                      <span className="line-clamp-2">{sch.return_service_obligation}</span>
                    </div>
                  )}
                </div>

                {/* Card Footer: Application Window & Action */}
                <div className="mt-5 pt-4 border-t border-white/[0.08] flex items-center justify-between gap-2">
                  <div className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{sch.application_window_start} – {sch.application_window_end.split(" ")[0]}</span>
                  </div>

                  <button
                    onClick={() => setModalScholarship(sch)}
                    className="inline-flex items-center gap-1 rounded-xl border border-white/15 bg-white/[0.06] px-3 py-1.5 text-xs font-semibold text-white hover:bg-orange-500 hover:border-orange-500 hover:text-white active:scale-95 transition-all"
                  >
                    <span>View Dossier</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Modal Dossier */}
      {modalScholarship && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl border border-white/20 bg-[#0c0d1b] p-6 sm:p-8 shadow-2xl space-y-6">
            <button
              onClick={() => setModalScholarship(null)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-white/10 text-white hover:bg-white/20 transition-all"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Modal Header */}
            <div className="space-y-2 pr-10">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase ${
                    modalScholarship.funding_type === "fully_funded"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  }`}
                >
                  {modalScholarship.funding_type === "fully_funded" ? "100% Fully Funded" : "Tuition Reduction"}
                </span>

                <span className="text-xs text-slate-400 font-semibold">
                  {modalScholarship.country_name}
                </span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
                {modalScholarship.name}
              </h2>
              <p className="text-sm text-slate-400">{modalScholarship.provider}</p>
            </div>

            {/* Coverage Summary Box */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-orange-400 flex items-center gap-1.5">
                <Coins className="h-4 w-4" /> Full Funding Coverage
              </h3>
              <p className="text-sm text-slate-200 leading-relaxed">
                {modalScholarship.coverage_summary}
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-2.5 text-xs">
                  <span className="text-slate-400 block">Tuition Waiver:</span>
                  <span className="font-bold text-white">{modalScholarship.tuition_coverage_pct}%</span>
                </div>

                <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-2.5 text-xs">
                  <span className="text-slate-400 block">Stipend:</span>
                  <span className="font-bold text-white">{modalScholarship.stipend_monthly_local || "None"}</span>
                </div>

                <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-2.5 text-xs">
                  <span className="text-slate-400 block">Housing:</span>
                  <span className="font-bold text-white">{modalScholarship.housing_covered ? "Covered" : "Self-funded"}</span>
                </div>
              </div>
            </div>

            {/* Mandatory Post-Graduation Obligation */}
            {modalScholarship.return_service_obligation && (
              <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300 uppercase">
                  <ShieldAlert className="h-4 w-4" /> Mandatory Service or Return Obligation
                </div>
                <p className="text-xs text-amber-200 leading-relaxed">
                  {modalScholarship.return_service_obligation}
                </p>
              </div>
            )}

            {/* Key Eligibility Criteria */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <UserCheck className="h-4 w-4 text-emerald-400" /> Key Statutory Eligibility Criteria
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {modalScholarship.eligibility_criteria.map((crit, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <span>{crit}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Required Documents Checklist */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-orange-400" /> Required Application Dossier
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {modalScholarship.required_documents.map((doc, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <ChevronRight className="h-3.5 w-3.5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <span>{doc}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Citation & Primary Source Provenance */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-[11px] text-slate-400 space-y-1">
              <span className="font-semibold text-slate-300">Statutory Citation:</span>
              <p>{modalScholarship.citation}</p>
            </div>

            {/* Modal Footer Link */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-white/10">
              <span className="text-xs text-slate-400">
                Cycle: {modalScholarship.application_window_start} to {modalScholarship.application_window_end}
              </span>

              <a
                href={modalScholarship.official_portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-5 py-2.5 text-xs font-bold text-white hover:brightness-110 active:scale-95 transition-all shadow-lg"
              >
                <span>Open Official Application Portal</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
