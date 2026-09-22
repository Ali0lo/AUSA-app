"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  SopAnalysisResult,
  CvAnalysisResult,
  FALLBACK_SOP_TEMPLATES,
  analyzeSopLocal,
  analyzeCvLocal,
  analyzeSop,
  analyzeCv,
} from "@/lib/sop-api";

export function SopChecker() {
  const [activeTab, setActiveTab] = useState<"sop" | "cv">("sop");

  // SOP State
  const [sopText, setSopText] = useState<string>(FALLBACK_SOP_TEMPLATES[0].content);
  const [wordMin, setWordMin] = useState<number>(500);
  const [wordMax, setWordMax] = useState<number>(1000);
  const [isStateProgramme, setIsStateProgramme] = useState<boolean>(true);
  const [sopResult, setSopResult] = useState<SopAnalysisResult>(() =>
    analyzeSopLocal({ text: FALLBACK_SOP_TEMPLATES[0].content, word_limit_min: 500, word_limit_max: 1000, is_state_programme: true })
  );

  // CV State
  const sampleCv = `Ali Iskandarli
Baku, Azerbaijan | ali@example.com | github.com/Ali0lo

Education
- BSc in Computer Engineering, Baku Higher Oil School, GPA: 3.9/4.0 (2022 - 2026)

Professional Experience
- Spearheaded telemetry processing microservices handling 50,000 events/minute at SOCAR Digital.
- Engineered automated anomaly detection algorithms reducing equipment downtime by 28%.
- Optimized distributed training clusters improving GPU throughput by 35%.
- Streamlined CI/CD deployment pipelines across 6 mission-critical microservices.
- Automated end-to-end integration testing suites pushing coverage to 92%.

Research & Selected Projects
- Authored undergraduate thesis on edge neural network quantization achieving 42% model compression.
- Built open-source distributed key-value cache handling 100,000 concurrent websocket connections.

Technical Skills
- Python, TypeScript, Go, PostgreSQL, Docker, Kubernetes, PyTorch`;

  const [cvText, setCvText] = useState<string>(sampleCv);
  const [cvResult, setCvResult] = useState<CvAnalysisResult>(() =>
    analyzeCvLocal({ text: sampleCv })
  );

  // Debounced API evaluation
  useEffect(() => {
    let isMounted = true;
    const timer = setTimeout(async () => {
      if (activeTab === "sop") {
        if (!sopText.trim()) return;
        const res = await analyzeSop({
          text: sopText,
          word_limit_min: wordMin,
          word_limit_max: wordMax,
          is_state_programme: isStateProgramme,
        });
        if (isMounted) setSopResult(res);
      } else {
        if (!cvText.trim()) return;
        const res = await analyzeCv({ text: cvText });
        if (isMounted) setCvResult(res);
      }
    }, 250);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [sopText, wordMin, wordMax, isStateProgramme, cvText, activeTab]);

  const handleLoadTemplate = (templateId: string) => {
    const t = FALLBACK_SOP_TEMPLATES.find((x) => x.id === templateId);
    if (t) {
      setSopText(t.content);
    }
  };

  const currentScore = activeTab === "sop" ? sopResult.overall_score : cvResult.overall_score;
  const currentGrade = activeTab === "sop" ? sopResult.letter_grade : cvResult.letter_grade;
  const currentVerdict = activeTab === "sop" ? sopResult.verdict : cvResult.verdict;

  // Circular gauge
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeOffset = circumference - (currentScore / 100) * circumference;

  return (
    <div className="space-y-8">
      {/* Top Controls & Navigation Bar */}
      <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-[#13152d]/90 to-[#0c0d1b]/90 p-6 md:p-8 backdrop-blur-xl shadow-2xl space-y-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          {/* Mode Switcher */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Sənəd Növünü Seçin
            </label>
            <div className="inline-flex rounded-xl bg-white/5 p-1 border border-white/10">
              <button
                type="button"
                onClick={() => setActiveTab("sop")}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition-all ${
                  activeTab === "sop"
                    ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/25"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                📝 Statement of Purpose (SOP)
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("cv")}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition-all ${
                  activeTab === "cv"
                    ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/25"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                📄 Academic CV / Resume
              </button>
            </div>
          </div>

          {/* Quick Template Selector */}
          {activeTab === "sop" && (
            <div className="space-y-2">
              <label htmlFor="template-select" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Nümunə Şablon Yüklə
              </label>
              <div className="flex flex-wrap gap-2">
                <select
                  id="template-select"
                  onChange={(e) => handleLoadTemplate(e.target.value)}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white backdrop-blur-md focus:border-orange-500 focus:outline-none"
                  defaultValue=""
                >
                  <option value="" disabled>
                    A-Grade Nümunə Seçin...
                  </option>
                  {FALLBACK_SOP_TEMPLATES.map((t) => (
                    <option key={t.id} value={t.id} className="bg-[#121327] text-white">
                      {t.title} ({t.word_count} söz)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* SOP Specific Parameter Sliders */}
        {activeTab === "sop" && (
          <div className="pt-4 border-t border-white/10 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-4">
              <span className="text-slate-400">Hədəf Söz Sayı:</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={200}
                  max={1500}
                  step={50}
                  value={wordMin}
                  onChange={(e) => setWordMin(parseInt(e.target.value) || 500)}
                  className="w-16 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-center text-white font-mono focus:border-orange-500 focus:outline-none"
                />
                <span className="text-slate-500">—</span>
                <input
                  type="number"
                  min={300}
                  max={2500}
                  step={50}
                  value={wordMax}
                  onChange={(e) => setWordMax(parseInt(e.target.value) || 1000)}
                  className="w-16 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-center text-white font-mono focus:border-orange-500 focus:outline-none"
                />
                <span className="text-slate-400">söz</span>
              </div>
            </div>

            <label className="flex items-center gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={isStateProgramme}
                onChange={(e) => setIsStateProgramme(e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-white/5 text-orange-500 focus:ring-0 cursor-pointer"
              />
              <span className="text-slate-300 font-medium">
                🇦🇿 2022–2026 Dövlət Proqramı Müsabiqəsi Tələbləri (Ölkəyə Töhfə Maddəsi)
              </span>
            </label>
          </div>
        )}
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left: Textarea Editor (7 cols) */}
        <div className="space-y-4 lg:col-span-7">
          <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3 text-xs">
              <div className="flex items-center gap-4 text-slate-400">
                <span>
                  Söz:{" "}
                  <strong className="text-white font-mono">
                    {activeTab === "sop" ? sopResult.word_count : cvResult.word_count}
                  </strong>
                </span>
                <span>
                  Simvol:{" "}
                  <strong className="text-white font-mono">
                    {activeTab === "sop" ? sopResult.char_count : cvText.length}
                  </strong>
                </span>
                {activeTab === "sop" && (
                  <span>
                    Abzas:{" "}
                    <strong className="text-white font-mono">{sopResult.paragraph_count}</strong>
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (activeTab === "sop") setSopText("");
                    else setCvText("");
                  }}
                  className="rounded-lg px-2.5 py-1 text-slate-400 hover:bg-white/10 hover:text-white transition-all text-xs"
                >
                  Təmizlə
                </button>
              </div>
            </div>

            <textarea
              rows={18}
              value={activeTab === "sop" ? sopText : cvText}
              onChange={(e) => {
                if (activeTab === "sop") setSopText(e.target.value);
                else setCvText(e.target.value);
              }}
              placeholder={
                activeTab === "sop"
                  ? "Statement of Purpose və ya motivasiya məktubunuzu bura yapışdırın..."
                  : "Academic CV mətninizi bura yapışdırın..."
              }
              className="w-full rounded-2xl border border-white/5 bg-black/30 p-4 font-mono text-sm leading-relaxed text-slate-200 placeholder-slate-500 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />

            {activeTab === "sop" && (
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <span>
                  Oxunma müddəti: ~<strong>{sopResult.reading_time_minutes} dəqiqə</strong>
                </span>
                <span>
                  Məchul növ:{" "}
                  <strong
                    className={
                      sopResult.passive_voice_percentage > 25 ? "text-amber-400" : "text-emerald-400"
                    }
                  >
                    {sopResult.passive_voice_percentage}%
                  </strong>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Rubric Grade & Feedback (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Circular Grade Gauge Card */}
          <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-[#161836] to-[#0c0d1b] p-6 backdrop-blur-xl shadow-2xl text-center space-y-5">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              {activeTab === "sop" ? "SOP Qiymətləndirmə Rubrikası" : "Academic CV Qiymətləndirməsi"}
            </h3>

            <div className="relative mx-auto flex h-44 w-44 items-center justify-center">
              <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 160 160">
                <circle
                  cx="80"
                  cy="80"
                  r={radius}
                  stroke="currentColor"
                  strokeWidth="10"
                  fill="transparent"
                  className="text-white/5"
                />
                <circle
                  cx="80"
                  cy="80"
                  r={radius}
                  stroke="url(#sop-grade-gradient)"
                  strokeWidth="10"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeOffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-500 ease-out"
                />
                <defs>
                  <linearGradient id="sop-grade-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FF7A00" />
                    <stop offset="50%" stopColor="#F59E0B" />
                    <stop offset="100%" stopColor="#10B981" />
                  </linearGradient>
                </defs>
              </svg>

              <div className="absolute flex flex-col items-center">
                <span className="text-4xl font-extrabold tracking-tight text-white font-mono">
                  {currentGrade}
                </span>
                <span className="text-xs font-semibold text-slate-400 mt-0.5">
                  {currentScore} / 100 bal
                </span>
              </div>
            </div>

            {/* Verdict Banner */}
            <div
              className={`rounded-2xl border p-3.5 text-xs font-semibold text-left ${
                currentGrade === "A"
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                  : currentGrade === "B"
                  ? "border-blue-500/30 bg-blue-500/10 text-blue-300"
                  : currentGrade === "C"
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
                  : "border-red-500/30 bg-red-500/10 text-red-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <span>{currentGrade === "A" ? "🌟" : currentGrade === "B" ? "🟢" : "⚠️"}</span>
                <span>{currentVerdict}</span>
              </div>
            </div>

            {/* Category Progress Sub-scores (SOP Mode) */}
            {activeTab === "sop" && sopResult.category_scores && (
              <div className="space-y-2.5 text-left text-xs pt-2 border-t border-white/10">
                <SubScoreRow
                  label="Uzunluq və Abzas Qaydası"
                  score={sopResult.category_scores.length_hygiene}
                  max={20}
                />
                <SubScoreRow
                  label="Şablonsuz Orijinallıq"
                  score={sopResult.category_scores.cliche_originality}
                  max={20}
                />
                <SubScoreRow
                  label="Məlum Növ & Fəaliyyət Felləri"
                  score={sopResult.category_scores.voice_active_verbs}
                  max={15}
                />
                <SubScoreRow
                  label="Ölçülə Bilən Nəticələr (Metrics)"
                  score={sopResult.category_scores.readability_metrics}
                  max={10}
                />
                <SubScoreRow
                  label="Zəruri Hissələrin Əhatəsi"
                  score={sopResult.category_scores.narrative_sections}
                  max={35}
                />
              </div>
            )}
          </div>

          {/* Mandatory Narrative Sections (SOP Mode) */}
          {activeTab === "sop" && (
            <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl shadow-2xl space-y-4">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>📑</span>
                <span>Zəruri Esse Hissələri</span>
              </h4>

              <div className="space-y-3">
                {sopResult.sections.map((sec) => (
                  <div
                    key={sec.section_key}
                    className="rounded-xl border border-white/5 bg-white/[0.02] p-3 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-white">{sec.name}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${
                          sec.status === "STRONG"
                            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                            : sec.status === "PRESENT"
                            ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-400"
                            : sec.status === "WEAK"
                            ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                            : "border-red-500/30 bg-red-500/10 text-red-400"
                        }`}
                      >
                        {sec.status === "STRONG"
                          ? "Əla"
                          : sec.status === "PRESENT"
                          ? "Mövcuddur"
                          : sec.status === "WEAK"
                          ? "Zəif"
                          : "Çatışmır"}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{sec.feedback}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CV Specific Metrics */}
          {activeTab === "cv" && (
            <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl shadow-2xl space-y-4 text-xs">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span>📊</span>
                <span>CV Bənd və Metrika Analizi</span>
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-white/5 p-3 border border-white/10 space-y-1">
                  <span className="text-slate-400">Ümumi Bəndlər</span>
                  <p className="text-lg font-bold text-white font-mono">{cvResult.bullet_count}</p>
                </div>
                <div className="rounded-xl bg-white/5 p-3 border border-white/10 space-y-1">
                  <span className="text-slate-400">Rəqəmlə Ölçülən</span>
                  <p className="text-lg font-bold text-emerald-400 font-mono">
                    {cvResult.quantified_bullets_count}
                  </p>
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <span className="text-slate-400 font-medium">Aşkarlanmış Bölmələr:</span>
                <div className="flex flex-wrap gap-1.5">
                  {cvResult.sections_detected.map((s) => (
                    <span
                      key={s}
                      className="rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                    >
                      ✓ {s}
                    </span>
                  ))}
                  {cvResult.missing_sections.map((s) => (
                    <span
                      key={s}
                      className="rounded-md bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                    >
                      ✗ {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Actionable Suggestions & Cliché Detection Cards */}
      <section className="space-y-4 pt-4 border-t border-white/10">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span>💡</span>
          <span>Təkmilləşdirmə Tövsiyələri</span>
          <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs text-slate-300">
            {activeTab === "sop" ? sopResult.issues.length : cvResult.issues.length} qeyd
          </span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(activeTab === "sop" ? sopResult.issues : cvResult.issues).map((issue) => (
            <div
              key={issue.id}
              className={`rounded-2xl border p-5 backdrop-blur-xl space-y-2 transition-all hover:bg-white/[0.04] ${
                issue.severity === "CRITICAL"
                  ? "border-red-500/30 bg-red-500/[0.05]"
                  : issue.severity === "WARNING"
                  ? "border-amber-500/30 bg-amber-500/[0.05]"
                  : "border-blue-500/30 bg-blue-500/[0.05]"
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <span
                  className={`font-bold ${
                    issue.severity === "CRITICAL"
                      ? "text-red-400"
                      : issue.severity === "WARNING"
                      ? "text-amber-400"
                      : "text-blue-400"
                  }`}
                >
                  {issue.category}
                </span>
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-slate-400 uppercase tracking-widest">
                  {issue.severity}
                </span>
              </div>

              <p className="text-sm font-semibold text-white">{issue.message}</p>

              {issue.suggestion && (
                <div className="rounded-xl bg-black/30 p-3 text-xs text-slate-300 border border-white/5 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400">
                    Tövsiyə olunan düzəliş:
                  </span>
                  <p className="leading-relaxed">{issue.suggestion}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function SubScoreRow({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px]">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-200 font-mono font-bold">
          {score} / {max}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-orange-500 to-emerald-400 transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
