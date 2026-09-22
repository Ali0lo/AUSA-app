"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  MilestoneItem,
  MilestoneFilter,
  TimelineSchedule,
  UrgencyLevel,
  DegreeLevel,
  IntakeSeason,
  fetchMilestones,
  getLocalTimelineSchedule,
  generateClientIcs,
  downloadIcsFile,
} from "@/lib/timeline-api";

const COUNTRY_FILTERS = [
  { code: "", label: "Bütün Ölkələr", flag: "🌍" },
  { code: "AZ", label: "Dövlət Proqramı", flag: "🇦🇿" },
  { code: "GB", label: "Böyük Britaniya", flag: "🇬🇧" },
  { code: "DE", label: "Almaniya", flag: "🇩🇪" },
  { code: "US", label: "ABŞ", flag: "🇺🇸" },
  { code: "TR", label: "Türkiyə", flag: "🇹🇷" },
  { code: "IT", label: "İtaliya", flag: "🇮🇹" },
  { code: "HU", label: "Macarıstan", flag: "🇭🇺" },
  { code: "FR", label: "Fransa", flag: "🇫🇷" },
  { code: "PL", label: "Polşa", flag: "🇵🇱" },
];

export function AdmissionsTimeline() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedLevel, setSelectedLevel] = useState<DegreeLevel>("all");
  const [selectedIntake, setSelectedIntake] = useState<string>("all");
  const [selectedUrgency, setSelectedUrgency] = useState<string>("all");
  const [stateProgrammeOnly, setStateProgrammeOnly] = useState(false);
  const [showCustomModal, setShowCustomModal] = useState(false);

  // Custom reminder modal state
  const [customTitle, setCustomTitle] = useState("");
  const [customDate, setCustomDate] = useState("");
  const [customCountry, setCustomCountry] = useState("Beynəlxalq");
  const [customNotes, setCustomNotes] = useState("");
  const [customDaysBefore, setCustomDaysBefore] = useState(3);

  const schedule = useMemo(() => {
    return getLocalTimelineSchedule({
      country_code: selectedCountry || undefined,
      degree_level: selectedLevel !== "all" ? selectedLevel : undefined,
      intake: selectedIntake !== "all" ? (selectedIntake as IntakeSeason) : undefined,
      urgency: selectedUrgency !== "all" ? (selectedUrgency as UrgencyLevel) : undefined,
      is_state_programme_eligible: stateProgrammeOnly ? true : undefined,
      search_query: searchQuery.trim() || undefined,
    });
  }, [searchQuery, selectedCountry, selectedLevel, selectedIntake, selectedUrgency, stateProgrammeOnly]);

  const handleExportAll = () => {
    if (!schedule.milestones.length) return;
    const icsString = generateClientIcs(schedule.milestones, "AUSA Seçilmiş Dedlaynlar 2026/2027");
    downloadIcsFile("ausa-admissions-schedule.ics", icsString);
  };

  const handleExportSingle = (item: MilestoneItem) => {
    const icsString = generateClientIcs([item], item.title);
    downloadIcsFile(`ausa-${item.id}.ics`, icsString);
  };

  const handleCreateCustomReminder = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTitle || !customDate) return;

    const fakeItem: MilestoneItem = {
      id: `custom_${Date.now()}`,
      title: customTitle,
      portal_name: customCountry,
      country_code: "GLOBAL",
      country_name: customCountry,
      flag: "📌",
      degree_level: "all",
      intake: "fall_2026",
      milestone_type: "REGULAR_DEADLINE",
      target_date: customDate,
      deadline_time: "23:59",
      description: customNotes || "Fərdi qeyd olunmuş universitet müraciət tarixi.",
      official_portal_url: "",
      requirements_summary: [],
      is_hard_deadline: true,
      days_remaining: 0,
      urgency: "OPEN",
      is_state_programme_eligible: false,
    };

    const icsString = generateClientIcs([fakeItem], customTitle);
    downloadIcsFile(`ausa-reminder-${fakeItem.id}.ics`, icsString);

    setShowCustomModal(false);
    setCustomTitle("");
    setCustomDate("");
    setCustomNotes("");
  };

  const criticalItems = useMemo(
    () => schedule.milestones.filter((m) => m.urgency === "CRITICAL" || m.urgency === "UPCOMING"),
    [schedule.milestones]
  );

  return (
    <div className="space-y-8">
      {/* Top Hero Card & Statistics */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-[#13152d] to-[#0c0d1b] p-6 md:p-8 backdrop-blur-xl shadow-2xl space-y-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold text-orange-400">
              <span className="h-2 w-2 rounded-full bg-orange-400 animate-pulse" />
              2026/2027 Qəbul Dövriyyəsi Təqvimi
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
              Qəbul & Təqaüd Dedlayn İzləyicisi
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-slate-400">
              Böyük Britaniya (UCAS), Almaniya (Uni-Assist/VPD), ABŞ (Common App), 2022–2026 Dövlət Proqramı,
              Türkiyə Bursları və İtaliya DSU üzrə rəsmi tarixlər və Google/Apple Calendar (.ics) inteqrasiyası.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleExportAll}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-orange-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <span>📅</span>
              <span>Bütün Dedlaynları Təqvimə Yazdır (.ics)</span>
            </button>
            <button
              type="button"
              onClick={() => setShowCustomModal(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-bold text-slate-300 hover:bg-white/10 hover:text-white transition-all"
            >
              <span>➕</span>
              <span>Fərdi Dedlayn Əlavə Et</span>
            </button>
          </div>
        </div>

        {/* Real-time stats row */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10 sm:grid-cols-4">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-3 text-center">
            <span className="text-[11px] font-semibold text-slate-400">Ümumi Tarixlər</span>
            <p className="text-2xl font-black text-white font-mono mt-0.5">{schedule.total_milestones}</p>
          </div>
          <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.03] p-3 text-center">
            <span className="text-[11px] font-semibold text-red-400">Təcili (&le; 14 gün)</span>
            <p className="text-2xl font-black text-red-400 font-mono mt-0.5">{schedule.critical_count}</p>
          </div>
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/[0.03] p-3 text-center">
            <span className="text-[11px] font-semibold text-amber-400">Yaxınlaşan (&le; 60 gün)</span>
            <p className="text-2xl font-black text-amber-400 font-mono mt-0.5">{schedule.upcoming_count}</p>
          </div>
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.03] p-3 text-center">
            <span className="text-[11px] font-semibold text-emerald-400">Açıq Pəncərələr</span>
            <p className="text-2xl font-black text-emerald-400 font-mono mt-0.5">{schedule.open_count}</p>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="rounded-3xl border border-white/10 bg-[#121327]/80 p-6 backdrop-blur-xl shadow-2xl space-y-5">
        {/* Search bar & Dropdowns */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
          <div className="md:col-span-5">
            <input
              type="text"
              placeholder="Portal, universitet, şəhər və ya imtahan axtar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-orange-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-3 gap-2 md:col-span-7">
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value as DegreeLevel)}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-xs font-medium text-white focus:border-orange-500 focus:outline-none"
            >
              <option value="all" className="bg-[#121327]">Bütün Səviyyələr</option>
              <option value="bachelor" className="bg-[#121327]">Bakalavr</option>
              <option value="master" className="bg-[#121327]">Magistr</option>
            </select>

            <select
              value={selectedIntake}
              onChange={(e) => setSelectedIntake(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-xs font-medium text-white focus:border-orange-500 focus:outline-none"
            >
              <option value="all" className="bg-[#121327]">Bütün Qəbul Dövləri</option>
              <option value="fall_2026" className="bg-[#121327]">Fall 2026 (Payız)</option>
              <option value="spring_2027" className="bg-[#121327]">Spring 2027 (Yaz)</option>
              <option value="fall_2027" className="bg-[#121327]">Fall 2027</option>
            </select>

            <select
              value={selectedUrgency}
              onChange={(e) => setSelectedUrgency(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-xs font-medium text-white focus:border-orange-500 focus:outline-none"
            >
              <option value="all" className="bg-[#121327]">Bütün Statuslar</option>
              <option value="CRITICAL" className="bg-[#121327]">🔴 Təcili (&le;14 gün)</option>
              <option value="UPCOMING" className="bg-[#121327]">🟡 Yaxınlaşan</option>
              <option value="OPEN" className="bg-[#121327]">🟢 Açıq</option>
              <option value="PASSED" className="bg-[#121327]">⚪ Keçmiş</option>
            </select>
          </div>
        </div>

        {/* Country Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex flex-wrap items-center gap-1.5">
            {COUNTRY_FILTERS.map((c) => {
              const active = selectedCountry === c.code;
              return (
                <button
                  key={c.code}
                  type="button"
                  onClick={() => setSelectedCountry(c.code)}
                  className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition-all ${
                    active
                      ? "bg-white text-[#0c0d1b] shadow-md shadow-white/10"
                      : "bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <span className="mr-1.5">{c.flag}</span>
                  <span>{c.label}</span>
                </button>
              );
            })}
          </div>

          <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-slate-300">
            <input
              type="checkbox"
              checked={stateProgrammeOnly}
              onChange={(e) => setStateProgrammeOnly(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-white/5 text-orange-500 focus:ring-0 cursor-pointer"
            />
            <span>🇦🇿 Yalnız Dövlət Proqramına Uyğun</span>
          </label>
        </div>
      </div>

      {/* Urgent Warning Banners */}
      {criticalItems.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-orange-400 flex items-center gap-2">
            <span>⚡</span>
            <span>Diqqət Tələb Edən Ən Yaxın Dedlaynlar</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {criticalItems.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 via-amber-500/5 to-transparent p-4 backdrop-blur-xl space-y-2 relative group"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <span>{item.flag}</span>
                    <span>{item.country_name}</span>
                  </span>
                  <span className="rounded-full bg-orange-500/20 px-2 py-0.5 text-[10px] font-bold text-orange-300 border border-orange-500/30">
                    {item.days_remaining >= 0 ? `${item.days_remaining} gün qaldı` : "Tarix keçib"}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white line-clamp-1 group-hover:text-orange-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">
                  Son tarix: <strong className="text-slate-200">{item.target_date}</strong> ({item.deadline_time})
                </p>
                <div className="pt-2 flex items-center justify-between">
                  <a
                    href={item.official_portal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-orange-400 hover:text-orange-300 underline font-medium"
                  >
                    Rəsmi Portal &rarr;
                  </a>
                  <button
                    type="button"
                    onClick={() => handleExportSingle(item)}
                    className="rounded-lg bg-white/10 px-2 py-1 text-[10px] font-bold text-white hover:bg-white/20 transition-all"
                  >
                    Təqvimə Yazdır (.ics)
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chronological Milestone Stream */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🗓️</span>
            <span>Xronoloji Qəbul & Təqaüd Axını</span>
            <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs text-slate-300">
              {schedule.milestones.length} mərhələ
            </span>
          </h2>
        </div>

        {schedule.milestones.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-[#121327]/40 p-12 text-center text-slate-400 space-y-3">
            <span className="text-4xl">🔍</span>
            <p className="text-sm">Seçilmiş filtrlərə uyğun heç bir qəbul tarixi tapılmadı.</p>
            <button
              type="button"
              onClick={() => {
                setSelectedCountry("");
                setSelectedLevel("all");
                setSelectedIntake("all");
                setSelectedUrgency("all");
                setStateProgrammeOnly(false);
                setSearchQuery("");
              }}
              className="text-xs text-orange-400 underline font-semibold"
            >
              Bütün filtrləri sıfırla
            </button>
          </div>
        ) : (
          <div className="relative border-l-2 border-white/10 ml-4 md:ml-6 space-y-6 py-2">
            {schedule.milestones.map((m) => {
              const isCritical = m.urgency === "CRITICAL";
              const isUpcoming = m.urgency === "UPCOMING";
              const isPassed = m.urgency === "PASSED";

              return (
                <div key={m.id} className="relative pl-6 md:pl-8 group">
                  {/* Timeline Node Icon */}
                  <span
                    className={`absolute -left-[9px] top-1.5 h-4 w-4 rounded-full border-2 transition-all ${
                      isCritical
                        ? "border-red-500 bg-red-400 shadow-lg shadow-red-500/50 scale-110"
                        : isUpcoming
                        ? "border-amber-500 bg-amber-400 shadow-md shadow-amber-500/30"
                        : isPassed
                        ? "border-slate-600 bg-slate-700"
                        : "border-emerald-500 bg-emerald-400 shadow-md shadow-emerald-500/30"
                    }`}
                  />

                  {/* Card Body */}
                  <div
                    className={`rounded-2xl border p-5 backdrop-blur-xl transition-all hover:bg-white/[0.04] space-y-3 ${
                      isCritical
                        ? "border-red-500/30 bg-red-500/[0.03]"
                        : isUpcoming
                        ? "border-amber-500/20 bg-amber-500/[0.02]"
                        : "border-white/10 bg-[#121327]/80"
                    }`}
                  >
                    {/* Top Badges */}
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{m.flag}</span>
                        <span className="font-semibold text-white">{m.country_name}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-400">{m.portal_name}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold border ${
                            isCritical
                              ? "border-red-500/30 bg-red-500/10 text-red-400"
                              : isUpcoming
                              ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                              : isPassed
                              ? "border-slate-500/30 bg-slate-500/10 text-slate-400"
                              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                          }`}
                        >
                          {isPassed
                            ? "Keçib"
                            : m.days_remaining === 0
                            ? "Bu gün son tarixdir!"
                            : `${m.days_remaining} gün qaldı`}
                        </span>

                        {m.is_state_programme_eligible && (
                          <span className="rounded-full border border-orange-500/30 bg-orange-500/10 px-2 py-0.5 text-[10px] font-bold text-orange-400">
                            🇦🇿 DP Uyğundur
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Title & Description */}
                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-orange-300 transition-colors">
                        {m.title}
                      </h3>
                      <p className="mt-1 text-xs leading-relaxed text-slate-400">
                        {m.description}
                      </p>
                    </div>

                    {/* Requirements checklist */}
                    {m.requirements_summary?.length > 0 && (
                      <div className="rounded-xl border border-white/5 bg-black/20 p-3 text-xs space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          Zəruri Tələblər və Sənədlər:
                        </span>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-1 text-[11px] text-slate-300">
                          {m.requirements_summary.map((req, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-emerald-400 mt-0.5">✓</span>
                              <span>{req}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Card Footer: Date info & Buttons */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/5 text-xs">
                      <div className="flex items-center gap-3 font-mono text-slate-300">
                        <span>
                          📅 <strong className="text-white">{m.target_date}</strong>
                        </span>
                        <span>
                          ⏰ <strong className="text-slate-400">{m.deadline_time}</strong>
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {m.official_portal_url && (
                          <a
                            href={m.official_portal_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-all text-xs"
                          >
                            Rəsmi Portal &nearr;
                          </a>
                        )}
                        <button
                          type="button"
                          onClick={() => handleExportSingle(m)}
                          className="rounded-lg bg-orange-500/10 border border-orange-500/20 px-3 py-1.5 font-semibold text-orange-400 hover:bg-orange-500/20 transition-all text-xs"
                        >
                          Təqvimə Əlavə Et (.ics)
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Modal for Custom Personal Deadline */}
      {showCustomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-[#121327] p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>➕</span>
                <span>Fərdi Universitet Dedlaynı Əlavə Et</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowCustomModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateCustomReminder} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-semibold">Tədbir / Dedlayn Adı *</label>
                <input
                  type="text"
                  required
                  placeholder="Məs., TUM Informatiik Motivasiya Məktubu Son Tarixi"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-orange-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-300 font-semibold">Dedlayn Tarixi *</label>
                  <input
                    type="date"
                    required
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-300 font-semibold">Ölkə / Universitet</label>
                  <input
                    type="text"
                    placeholder="Məs., Almaniya / TUM"
                    value={customCountry}
                    onChange={(e) => setCustomCountry(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-semibold">Qeydlər & Zəruri Sənədlər</label>
                <textarea
                  rows={3}
                  placeholder="Məs., VPD sənədi, Attestat tərcüməsi, IELTS 7.0 sertifikatı"
                  value={customNotes}
                  onChange={(e) => setCustomNotes(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-orange-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-semibold">
                  Təqvim Xatırlatması (Dedlayndan neçə gün əvvəl):
                </label>
                <select
                  value={customDaysBefore}
                  onChange={(e) => setCustomDaysBefore(Number(e.target.value))}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-orange-500 focus:outline-none"
                >
                  <option value={1} className="bg-[#121327]">1 gün əvvəl</option>
                  <option value={3} className="bg-[#121327]">3 gün əvvəl (Tövsiyə olunur)</option>
                  <option value={7} className="bg-[#121327]">1 həftə əvvəl</option>
                  <option value={14} className="bg-[#121327]">2 həftə əvvəl</option>
                </select>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowCustomModal(false)}
                  className="rounded-xl px-4 py-2 text-slate-400 hover:text-white"
                >
                  Ləğv et
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-4 py-2 font-bold text-white shadow-lg shadow-orange-500/20"
                >
                  Təqvim Faylını Yarat (.ics)
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
