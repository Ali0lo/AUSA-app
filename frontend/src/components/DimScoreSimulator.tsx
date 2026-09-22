"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  DimGroup,
  SubGroup,
  ChanceLevel,
  BuraxilisInput,
  BlokInput,
  DimScoreBreakdown,
  SpecialtyRecommendation,
  DIM_GROUPS_META,
  getDefaultBuraxilisInput,
  getDefaultBlokInput,
  calculateLocalTotalDimScore,
  fetchSpecialtyRecommendations,
} from "@/lib/dim-api";

export function DimScoreSimulator() {
  const [selectedGroup, setSelectedGroup] = useState<DimGroup>("I qrup");
  const [selectedSubgroup, setSelectedSubgroup] = useState<SubGroup>("RI");
  const [inputMode, setInputMode] = useState<"detailed" | "direct">("detailed");

  // Inputs
  const [buraxilis, setBuraxilis] = useState<BuraxilisInput>(getDefaultBuraxilisInput());
  const [blok, setBlok] = useState<BlokInput>(getDefaultBlokInput("I qrup", "RI"));

  // Direct score inputs
  const [directBuraxilis, setDirectBuraxilis] = useState<number>(240);
  const [directBlok, setDirectBlok] = useState<number>(320);

  // Recommendations state
  const [recommendations, setRecommendations] = useState<SpecialtyRecommendation[]>([]);
  const [totalMatched, setTotalMatched] = useState<number>(0);
  // Set only when the cutoff history was missing or the API was unreachable. Held apart
  // from the recommendation list so an empty list can say WHY it is empty.
  const [corpusNote, setCorpusNote] = useState<string | null>(null);
  const [chanceFilter, setChanceFilter] = useState<ChanceLevel | "ALL">("ALL");
  const [selectedUniversity, setSelectedUniversity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoadingRecs, setIsLoadingRecs] = useState<boolean>(false);

  // When group changes, update subgroup and default subjects
  const currentGroupMeta = useMemo(() => {
    return DIM_GROUPS_META.find((g) => g.group === selectedGroup) || DIM_GROUPS_META[0];
  }, [selectedGroup]);

  const handleGroupChange = (g: DimGroup) => {
    setSelectedGroup(g);
    const meta = DIM_GROUPS_META.find((m) => m.group === g);
    const firstSub = (meta?.subgroups[0]?.code as SubGroup) || "NONE";
    setSelectedSubgroup(firstSub);
    setBlok(getDefaultBlokInput(g, firstSub));
  };

  const handleSubgroupChange = (sg: SubGroup) => {
    setSelectedSubgroup(sg);
    setBlok(getDefaultBlokInput(selectedGroup, sg));
  };

  // Synchronous local score calculation
  const scoreBreakdown: DimScoreBreakdown = useMemo(() => {
    if (inputMode === "direct") {
      const bInp: BuraxilisInput = {
        ...buraxilis,
        direct_total_score: directBuraxilis,
      };
      const blkInp: BlokInput = {
        ...blok,
        direct_total_score: directBlok,
      };
      return calculateLocalTotalDimScore({
        group: selectedGroup,
        subgroup: selectedSubgroup,
        buraxilis: bInp,
        blok: blkInp,
      });
    }

    return calculateLocalTotalDimScore({
      group: selectedGroup,
      subgroup: selectedSubgroup,
      buraxilis,
      blok,
    });
  }, [inputMode, buraxilis, blok, directBuraxilis, directBlok, selectedGroup, selectedSubgroup]);

  // Load recommendations
  useEffect(() => {
    let isMounted = true;

    const timer = setTimeout(async () => {
      setIsLoadingRecs(true);
      const res = await fetchSpecialtyRecommendations(
        {
          group: selectedGroup,
          subgroup: selectedSubgroup,
          candidate_score: scoreBreakdown.total_score,
          university_filter: selectedUniversity === "ALL" ? undefined : selectedUniversity,
          chance_filter: chanceFilter === "ALL" ? undefined : chanceFilter,
          search_query: searchQuery.trim() || undefined,
          limit: 60,
        },
        scoreBreakdown
      );

      if (isMounted) {
        setRecommendations(res.recommendations);
        setTotalMatched(res.total_matched);
        setCorpusNote(res.corpus_status && res.corpus_status !== "available" ? res.corpus_note ?? null : null);
        setIsLoadingRecs(false);
      }
    }, 200);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [selectedGroup, selectedSubgroup, scoreBreakdown.total_score, selectedUniversity, chanceFilter, searchQuery]);

  // SVG Gauge calculations
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const scorePct = Math.min(1, Math.max(0, scoreBreakdown.total_score / 700));
  const strokeDashoffset = circumference - scorePct * circumference;

  return (
    <div className="space-y-10">
      {/* Top Controller: Group Tabs & Mode */}
      <section aria-label="dim-controls" className="rounded-3xl border border-white/10 bg-gradient-to-b from-[#13152d]/90 to-[#0c0d1b]/90 p-6 md:p-8 backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          {/* Group Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              İxtisas Qrupunu Seçin
            </label>
            <div className="flex flex-wrap gap-2">
              {DIM_GROUPS_META.map((g) => {
                const active = selectedGroup === g.group;
                return (
                  <button
                    key={g.group}
                    type="button"
                    onClick={() => handleGroupChange(g.group)}
                    className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 ${
                      active
                        ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/25"
                        : "bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {g.name}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-slate-400 pt-1">{currentGroupMeta.description}</p>
          </div>

          {/* Mode Switcher */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Hesablama Rejimi
            </label>
            <div className="inline-flex rounded-xl bg-white/5 p-1 border border-white/10">
              <button
                type="button"
                onClick={() => setInputMode("detailed")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  inputMode === "detailed"
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Sual Sayı ilə
              </button>
              <button
                type="button"
                onClick={() => setInputMode("direct")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  inputMode === "direct"
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Dəqiq Bal ilə
              </button>
            </div>
          </div>
        </div>

        {/* Subgroup selector if group has options */}
        {currentGroupMeta.subgroups.length > 1 && (
          <div className="mt-6 pt-6 border-t border-white/10 flex flex-wrap items-center gap-3">
            <span className="text-xs font-medium text-slate-400">Alt İxtisas Qrupu:</span>
            {currentGroupMeta.subgroups.map((sg) => {
              const active = selectedSubgroup === sg.code;
              return (
                <button
                  key={sg.code}
                  type="button"
                  onClick={() => handleSubgroupChange(sg.code as SubGroup)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                    active
                      ? "bg-white/20 text-white border border-white/30"
                      : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-300"
                  }`}
                >
                  {sg.name}
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Main Grid: Inputs (Left) and Score Gauge (Right) */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left: Exam Inputs (7 cols) */}
        <div className="space-y-8 lg:col-span-7">
          {inputMode === "direct" ? (
            /* Direct Score Sliders */
            <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 md:p-8 backdrop-blur-xl space-y-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🎯</span> Dəqiq İmtahan Ballarınız
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <label htmlFor="direct-buraxilis-slider" className="text-slate-300 font-medium">Buraxılış İmtahanı Balı (Maks. 300)</label>
                  <span className="text-lg font-bold text-cyan-400">{directBuraxilis} bal</span>
                </div>
                <input
                  id="direct-buraxilis-slider"
                  type="range"
                  min={0}
                  max={300}
                  step={0.5}
                  value={directBuraxilis}
                  onChange={(e) => setDirectBuraxilis(parseFloat(e.target.value) || 0)}
                  className="w-full accent-cyan-400 h-2 bg-slate-700 rounded-lg cursor-pointer"
                />
              </div>

              <div className="space-y-4 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between text-sm">
                  <label htmlFor="direct-blok-slider" className="text-slate-300 font-medium">Blok İmtahanı Balı (Maks. 400)</label>
                  <span className="text-lg font-bold text-amber-400">{directBlok} bal</span>
                </div>
                <input
                  id="direct-blok-slider"
                  type="range"
                  min={0}
                  max={400}
                  step={0.5}
                  value={directBlok}
                  onChange={(e) => setDirectBlok(parseFloat(e.target.value) || 0)}
                  className="w-full accent-amber-400 h-2 bg-slate-700 rounded-lg cursor-pointer"
                />
              </div>
            </div>
          ) : (
            /* Detailed Question Breakdown */
            <div className="space-y-6">
              {/* Buraxilis Card */}
              <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl space-y-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <span className="text-cyan-400">1.</span> Buraxılış İmtahanı (Attestat)
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">3 fənn, maksimum 300 bal (4 səhv 1 düzü aparır)</p>
                  </div>
                  <span className="text-sm font-extrabold text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
                    {scoreBreakdown.buraxilis_score} / 300
                  </span>
                </div>

                <div className="space-y-5">
                  {/* Native Language */}
                  <SubjectInputRow
                    title={buraxilis.native_language.subject_name}
                    input={buraxilis.native_language}
                    result={scoreBreakdown.buraxilis_subjects[0]}
                    onChange={(updated) =>
                      setBuraxilis({ ...buraxilis, native_language: updated })
                    }
                  />
                  {/* Mathematics */}
                  <SubjectInputRow
                    title={buraxilis.mathematics.subject_name}
                    input={buraxilis.mathematics}
                    result={scoreBreakdown.buraxilis_subjects[1]}
                    onChange={(updated) =>
                      setBuraxilis({ ...buraxilis, mathematics: updated })
                    }
                  />
                  {/* Foreign Language */}
                  <SubjectInputRow
                    title={buraxilis.foreign_language.subject_name}
                    input={buraxilis.foreign_language}
                    result={scoreBreakdown.buraxilis_subjects[2]}
                    onChange={(updated) =>
                      setBuraxilis({ ...buraxilis, foreign_language: updated })
                    }
                  />
                </div>
              </div>

              {/* Blok Card */}
              <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl space-y-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <span className="text-amber-400">2.</span> İxtisas Bloku İmtahanı
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {selectedGroup} {selectedSubgroup !== "NONE" ? `(${selectedSubgroup})` : ""}, maksimum 400 bal
                    </p>
                  </div>
                  <span className="text-sm font-extrabold text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
                    {scoreBreakdown.blok_score} / 400
                  </span>
                </div>

                <div className="space-y-5">
                  {blok.subject_1 && (
                    <SubjectInputRow
                      title={blok.subject_1.subject_name}
                      input={blok.subject_1}
                      result={scoreBreakdown.blok_subjects[0]}
                      onChange={(updated) => setBlok({ ...blok, subject_1: updated })}
                    />
                  )}
                  {blok.subject_2 && (
                    <SubjectInputRow
                      title={blok.subject_2.subject_name}
                      input={blok.subject_2}
                      result={scoreBreakdown.blok_subjects[1]}
                      onChange={(updated) => setBlok({ ...blok, subject_2: updated })}
                    />
                  )}
                  {blok.subject_3 && (
                    <SubjectInputRow
                      title={blok.subject_3.subject_name}
                      input={blok.subject_3}
                      result={scoreBreakdown.blok_subjects[2]}
                      onChange={(updated) => setBlok({ ...blok, subject_3: updated })}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Score Visualizer & Status (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          <div className="sticky top-24 rounded-3xl border border-white/10 bg-gradient-to-b from-[#161836] to-[#0c0d1b] p-6 md:p-8 backdrop-blur-xl shadow-2xl text-center space-y-6">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              Yekun DİM Nəticəsi
            </h3>

            {/* Circular Gauge */}
            <div className="relative mx-auto flex h-48 w-48 items-center justify-center">
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
                  stroke="url(#score-gradient)"
                  strokeWidth="10"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-500 ease-out"
                />
                <defs>
                  <linearGradient id="score-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FF7A00" />
                    <stop offset="50%" stopColor="#F59E0B" />
                    <stop offset="100%" stopColor="#10B981" />
                  </linearGradient>
                </defs>
              </svg>

              <div className="absolute flex flex-col items-center">
                <span className="text-4xl font-extrabold tracking-tight text-white">
                  {scoreBreakdown.total_score}
                </span>
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  / 700 bal
                </span>
                <span className="mt-1 text-[11px] font-bold text-amber-400">
                  {scoreBreakdown.percentage}%
                </span>
              </div>
            </div>

            {/* Benchmark Badge */}
            <div>
              {scoreBreakdown.clears_bhos_benchmark ? (
                <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                    <span>⭐</span>
                    <span>BANM (BHOS) 650+ Həddini Keçir!</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Bakı Ali Neft Məktəbinin bütün dövlət sifarişli mühəndislik və İT ixtisasları üçün yüksək şans qazanırsınız.
                  </p>
                </div>
              ) : scoreBreakdown.total_score >= 550 ? (
                <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <span>🟢</span>
                    <span>Yüksək Rəqabət Qabiliyyəti (550+)</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    ADA, UNEC, BDU və BMU-nun aparıcı dövlət sifarişli ixtisasları üçün real qəbul şansı mövcuddur.
                  </p>
                </div>
              ) : scoreBreakdown.total_score >= 350 ? (
                <div className="rounded-2xl border border-blue-500/30 bg-blue-500/10 p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
                    <span>🔵</span>
                    <span>Müsabiqəyə Tam Uyğundur</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Dövlət sifarişi və ödənişli əsaslarla geniş ixtisas seçimi imkanı əldə edirsiniz.
                  </p>
                </div>
              ) : scoreBreakdown.passed_competition_minimum ? (
                <div className="rounded-2xl border border-purple-500/30 bg-purple-500/10 p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
                    <span>🟣</span>
                    <span>Minimum Hədd Keçildi (150+ bal)</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Ödənişli əsaslarla təhsil almaq üçün müsabiqədə iştirak hüququ qazanırsınız.
                  </p>
                </div>
              ) : (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
                    <span>⚠️</span>
                    <span>Müsabiqə Həddi (150 bal) Çatmır</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Universitetlərə sənəd vermək üçün ümumi bal ən azı 150 (dövlət sifarişi üçün 200) olmalıdır.
                  </p>
                </div>
              )}
            </div>

            {/* Split Progress Bars */}
            <div className="space-y-3 pt-2 text-left">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Buraxılış İmtahanı</span>
                  <span className="text-cyan-400">{scoreBreakdown.buraxilis_score} / 300</span>
                </div>
                <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-300"
                    style={{ width: `${(scoreBreakdown.buraxilis_score / 300) * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Blok İmtahanı</span>
                  <span className="text-amber-400">{scoreBreakdown.blok_score} / 400</span>
                </div>
                <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-300"
                    style={{ width: `${(scoreBreakdown.blok_score / 400) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Specialty Recommendations Section */}
      <section className="space-y-6 pt-4 border-t border-white/10">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-2xl font-bold text-white flex items-center gap-3">
              <span>🏛️</span>
              <span>Balınıza Uyğun İxtisaslar</span>
              <span className="rounded-full bg-white/10 px-3 py-0.5 text-xs font-medium text-slate-300">
                {totalMatched} ixtisas tapıldı
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              DİM-in 2023–2025-ci illər üzrə rəsmi keçid balları və müsabiqə statistikası əsasında hesablanmışdır.
            </p>
          </div>

          {/* Search Input */}
          <div className="w-full md:w-72">
            <input
              type="text"
              placeholder="İxtisas və ya universitet axtar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-400 backdrop-blur-md focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
          </div>
        </div>

        {/* Filter Chips Bar */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          {/* Chance Filters */}
          <button
            type="button"
            onClick={() => setChanceFilter("ALL")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              chanceFilter === "ALL"
                ? "bg-white/20 text-white border border-white/30"
                : "bg-white/5 text-slate-400 hover:text-slate-300"
            }`}
          >
            Hamısı
          </button>
          <button
            type="button"
            onClick={() => setChanceFilter("SAFE")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              chanceFilter === "SAFE"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "bg-white/5 text-slate-400 hover:text-slate-300"
            }`}
          >
            Yüksək Şans (Safe) 🟢
          </button>
          <button
            type="button"
            onClick={() => setChanceFilter("REALISTIC")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              chanceFilter === "REALISTIC"
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40"
                : "bg-white/5 text-slate-400 hover:text-slate-300"
            }`}
          >
            Real Şans 🔵
          </button>
          <button
            type="button"
            onClick={() => setChanceFilter("TARGET")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              chanceFilter === "TARGET"
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                : "bg-white/5 text-slate-400 hover:text-slate-300"
            }`}
          >
            Hədəf (Target) 🟡
          </button>
          <button
            type="button"
            onClick={() => setChanceFilter("ASPIRATIONAL")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              chanceFilter === "ASPIRATIONAL"
                ? "bg-red-500/20 text-red-400 border border-red-500/40"
                : "bg-white/5 text-slate-400 hover:text-slate-300"
            }`}
          >
            Çatışmır 🔴
          </button>

          <span className="text-white/20 mx-1">|</span>

          {/* University Filter Chips */}
          {["ALL", "BANM", "ADA", "UNEC", "BDU", "BMU", "ADNSU", "ATU"].map((u) => {
            const active = selectedUniversity === u;
            return (
              <button
                key={u}
                type="button"
                onClick={() => setSelectedUniversity(u)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  active
                    ? "bg-orange-500/20 text-orange-400 border border-orange-500/40"
                    : "bg-white/5 text-slate-400 hover:text-slate-300"
                }`}
              >
                {u === "ALL" ? "Bütün Universitetlər" : u}
              </button>
            );
          })}
        </div>

        {/* Rows drawn from the offline excerpt rather than the full cutoff history must
            say so, or the student reads a dozen programmes as the whole picture. */}
        {corpusNote && recommendations.length > 0 ? (
          <p className="rounded-2xl border border-amber-400/30 bg-amber-400/5 px-4 py-3 text-xs text-amber-200">
            {corpusNote}
          </p>
        ) : null}

        {/* Recommendations Table / Grid */}
        {isLoadingRecs ? (
          <div className="rounded-3xl border border-white/10 bg-[#121327]/60 p-12 text-center text-slate-400">
            İxtisaslar hesablanır...
          </div>
        ) : recommendations.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-[#121327]/60 p-12 text-center space-y-2">
            {corpusNote ? (
              <>
                {/* The list is empty for want of data, not for want of a match. Saying
                    "no specialties found" here would state a finding we cannot support. */}
                <p className="text-base text-amber-300 font-semibold">Keçid balı tarixçəsi mövcud deyil</p>
                <p className="text-xs text-slate-400">{corpusNote}</p>
              </>
            ) : (
              <>
                <p className="text-base text-slate-300 font-semibold">Heç bir ixtisas tapılmadı</p>
                <p className="text-xs text-slate-500">Filtrləri və ya axtarış sorğusunu dəyişib yenidən yoxlayın.</p>
              </>
            )}
          </div>
        ) : (
          <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#121327]/80 backdrop-blur-xl shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-white/10 bg-white/5 text-xs uppercase tracking-wider text-slate-400">
                  <tr>
                    <th scope="col" className="px-6 py-4">Universitet və İxtisas</th>
                    <th scope="col" className="px-4 py-4 text-center">2025 Keçid Balı</th>
                    <th scope="col" className="px-4 py-4 text-center">3 İllik Dinamika</th>
                    <th scope="col" className="px-4 py-4 text-center">Bal Fərqiniz</th>
                    <th scope="col" className="px-6 py-4 text-center">Qəbul Şansı</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {recommendations.map((rec) => {
                    const deltaPositive = rec.score_delta >= 0;
                    return (
                      <tr key={rec.program_code} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-base">
                                {rec.university_name}
                              </span>
                              {rec.is_bhos && (
                                <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/30">
                                  BANM 650+
                                </span>
                              )}
                              <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] text-slate-300">
                                {rec.scholarship_type}
                              </span>
                            </div>
                            <span className="text-xs text-slate-400 font-medium">
                              {rec.department_name}
                            </span>
                          </div>
                        </td>

                        <td className="px-4 py-4 text-center font-extrabold text-white">
                          {rec.cutoff_2025}
                        </td>

                        <td className="px-4 py-4 text-center">
                          {rec.three_year_trend ? (
                            <span
                              className={`text-xs font-bold ${
                                rec.three_year_trend.startsWith("+")
                                  ? "text-amber-400"
                                  : rec.three_year_trend === "stabil"
                                  ? "text-slate-400"
                                  : "text-emerald-400"
                              }`}
                            >
                              {rec.three_year_trend}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-600">—</span>
                          )}
                        </td>

                        <td className="px-4 py-4 text-center">
                          <span
                            className={`font-mono text-xs font-bold ${
                              deltaPositive ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {deltaPositive ? `+${rec.score_delta}` : rec.score_delta}
                          </span>
                        </td>

                        <td className="px-6 py-4 text-center">
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold border ${
                              rec.chance_level === "SAFE"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                : rec.chance_level === "REALISTIC"
                                ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                                : rec.chance_level === "TARGET"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                : "bg-red-500/10 text-red-400 border-red-500/30"
                            }`}
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-current" />
                            {rec.chance_level === "SAFE"
                              ? "Yüksək Şans"
                              : rec.chance_level === "REALISTIC"
                              ? "Real Şans"
                              : rec.chance_level === "TARGET"
                              ? "Hədəf (Həssas)"
                              : "Çatışmır"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

interface SubjectInputRowProps {
  title: string;
  input: import("@/lib/dim-api").SubjectQuestionInput;
  result?: import("@/lib/dim-api").SubjectScoreResult;
  onChange: (updated: import("@/lib/dim-api").SubjectQuestionInput) => void;
}

function SubjectInputRow({ title, input, result, onChange }: SubjectInputRowProps) {
  const scaledScore = result ? result.scaled_score : 0;

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 transition-all hover:border-white/10 hover:bg-white/[0.04] space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-white text-sm">{title}</span>
        <span className="text-xs font-bold text-slate-300 bg-white/10 px-2.5 py-0.5 rounded-md">
          {scaledScore} / {input.max_scaled_points} bal
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        {/* Closed Correct */}
        <div className="space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Düzgün (Qapalı)</span>
            <span className="text-slate-300 font-medium">/{input.max_closed}</span>
          </div>
          <input
            type="number"
            min={0}
            max={input.max_closed}
            value={input.closed_correct}
            onChange={(e) => {
              const val = Math.min(input.max_closed, Math.max(0, parseInt(e.target.value) || 0));
              onChange({
                ...input,
                closed_correct: val,
                closed_incorrect: Math.min(input.closed_incorrect, input.max_closed - val),
              });
            }}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-white font-mono focus:border-cyan-500 focus:outline-none"
          />
        </div>

        {/* Closed Incorrect */}
        <div className="space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Səhv (Qapalı)</span>
            <span className="text-slate-300 font-medium">4 səhv = -1</span>
          </div>
          <input
            type="number"
            min={0}
            max={input.max_closed - input.closed_correct}
            value={input.closed_incorrect}
            onChange={(e) => {
              const maxAllowed = input.max_closed - input.closed_correct;
              const val = Math.min(maxAllowed, Math.max(0, parseInt(e.target.value) || 0));
              onChange({ ...input, closed_incorrect: val });
            }}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-white font-mono focus:border-red-500 focus:outline-none"
          />
        </div>

        {/* Open Question Points */}
        <div className="space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Açıq Sual Balı</span>
            <span className="text-slate-300 font-medium">/{input.max_open_points}</span>
          </div>
          <input
            type="number"
            min={0}
            max={input.max_open_points}
            step={0.5}
            value={input.open_points}
            onChange={(e) => {
              const val = Math.min(input.max_open_points, Math.max(0, parseFloat(e.target.value) || 0));
              onChange({ ...input, open_points: val });
            }}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-white font-mono focus:border-amber-500 focus:outline-none"
          />
        </div>
      </div>
    </div>
  );
}
