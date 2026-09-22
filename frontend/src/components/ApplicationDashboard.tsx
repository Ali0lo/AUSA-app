"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  StudentApplicationItem,
  AdmissionTier,
  ApplicationStage,
  DocumentItem,
  DocumentChecklistResult,
  CURATED_BENCHMARKS,
  DEFAULT_APPLICATIONS,
  loadSavedApplications,
  saveApplicationsToStorage,
  getLocalDocumentChecklist,
} from "@/lib/application-tracker-api";
import { ComparisonMatrix } from "@/components/ComparisonMatrix";
import {
  LayoutDashboard,
  Plus,
  CheckCircle2,
  Calendar,
  Trash2,
  X,
  GraduationCap,
  Scale,
  CheckSquare,
  Square,
  Globe2,
  FileCheck,
} from "lucide-react";

const TIER_CONFIG: Record<
  AdmissionTier,
  { label: string; bg: string; border: string; text: string; dot: string }
> = {
  DREAM: {
    label: "Dream (Xəyal)",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-400",
    dot: "bg-purple-400",
  },
  TARGET: {
    label: "Target (Hədəf)",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    dot: "bg-blue-400",
  },
  SAFETY: {
    label: "Safety (Təhlükəsiz)",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
  },
};

const STAGE_LABELS: Record<ApplicationStage, string> = {
  shortlisted: "Seçilmişlər (Shortlisted)",
  document_gathering: "Sənəd Toplama",
  submitted: "Müraciət Göndərildi",
  under_review: "Baxılır",
  interview_scheduled: "Müsahibə Təyin Edildi",
  offer_received: "Qəbul Alındı 🎉",
  offer_accepted: "Qəbul Təsdiqləndi",
  rejected: "İmtina Edildi",
  visa_processing: "Viza Mərhələsi",
};

export function ApplicationDashboard() {
  const [applications, setApplications] = useState<StudentApplicationItem[]>(DEFAULT_APPLICATIONS);
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeChecklistApp, setActiveChecklistApp] = useState<StudentApplicationItem | null>(null);

  // New application form state
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>("");
  const [customUniName, setCustomUniName] = useState("");
  const [customProgram, setCustomProgram] = useState("");
  const [customCountry, setCustomCountry] = useState("DE");
  const [customCity, setCustomCity] = useState("");
  const [customTier, setCustomTier] = useState<AdmissionTier>("TARGET");
  const [customDeadline, setCustomDeadline] = useState("2026-07-15");

  // Load from localStorage on mount
  useEffect(() => {
    const saved = loadSavedApplications();
    if (saved && saved.length > 0) {
      setApplications(saved);
    }
  }, []);

  // Save to localStorage when modified
  const updateApplications = (newApps: StudentApplicationItem[]) => {
    setApplications(newApps);
    saveApplicationsToStorage(newApps);
  };

  // Stage change handler
  const handleStageChange = (appId: string, newStage: ApplicationStage) => {
    const updated = applications.map((app) =>
      app.id === appId ? { ...app, stage: newStage } : app
    );
    updateApplications(updated);
  };

  // Delete application handler
  const handleDeleteApp = (appId: string) => {
    const updated = applications.filter((app) => app.id !== appId);
    updateApplications(updated);
    if (activeChecklistApp?.id === appId) {
      setActiveChecklistApp(null);
    }
  };

  // Document checklist toggle
  const handleToggleDocument = (appId: string, docId: string) => {
    const updated = applications.map((app) => {
      if (app.id !== appId) return app;
      const currentCompleted = app.completed_doc_ids || [];
      const isDone = currentCompleted.includes(docId);
      const newCompleted = isDone
        ? currentCompleted.filter((id) => id !== docId)
        : [...currentCompleted, docId];

      return {
        ...app,
        completed_doc_ids: newCompleted,
      };
    });

    updateApplications(updated);

    const currentActive = updated.find((a) => a.id === appId);
    if (currentActive) {
      setActiveChecklistApp(currentActive);
    }
  };

  // Add application handler
  const handleAddApplication = (e: React.FormEvent) => {
    e.preventDefault();

    let newApp: StudentApplicationItem;

    if (selectedBenchmark && CURATED_BENCHMARKS[selectedBenchmark]) {
      const b = CURATED_BENCHMARKS[selectedBenchmark];
      newApp = {
        id: `app_${Date.now()}`,
        university_name: b.university_name,
        program_name: b.program_name,
        country_code: b.country_code,
        country_name: b.country_name,
        flag: b.flag,
        city: b.city,
        degree_level: b.degree_level,
        stage: "document_gathering",
        tier: b.admission_tier,
        deadline: "2026-07-15",
        tuition_eur_annual: b.tuition_eur_annual,
        living_cost_eur_monthly: b.living_cost_eur_monthly,
        completed_doc_ids: ["doc_passport"],
        notes: b.tier_rationale,
      };
    } else {
      if (!customUniName.trim() || !customProgram.trim()) return;
      const countryNames: Record<string, { name: string; flag: string }> = {
        DE: { name: "Almaniya", flag: "🇩🇪" },
        GB: { name: "Böyük Britaniya", flag: "🇬🇧" },
        IT: { name: "İtaliya", flag: "🇮🇹" },
        TR: { name: "Türkiyə", flag: "🇹🇷" },
        US: { name: "ABŞ", flag: "🇺🇸" },
        AZ: { name: "Azərbaycan", flag: "🇦🇿" },
      };
      const cMeta = countryNames[customCountry] || { name: customCountry, flag: "🌍" };

      newApp = {
        id: `app_${Date.now()}`,
        university_name: customUniName.trim(),
        program_name: customProgram.trim(),
        country_code: customCountry,
        country_name: cMeta.name,
        flag: cMeta.flag,
        city: customCity.trim() || "Mərkəz",
        degree_level: "master",
        stage: "document_gathering",
        tier: customTier,
        deadline: customDeadline,
        tuition_eur_annual: 10000,
        living_cost_eur_monthly: 900,
        completed_doc_ids: [],
      };
    }

    updateApplications([newApp, ...applications]);
    setShowAddModal(false);
    setSelectedBenchmark("");
    setCustomUniName("");
    setCustomProgram("");
  };

  // Filtered applications
  const filteredApps = useMemo(() => {
    if (tierFilter === "ALL") return applications;
    return applications.filter((app) => app.tier === tierFilter);
  }, [applications, tierFilter]);

  // Statistics
  const stats = useMemo(() => {
    const total = applications.length;
    const dream = applications.filter((a) => a.tier === "DREAM").length;
    const target = applications.filter((a) => a.tier === "TARGET").length;
    const safety = applications.filter((a) => a.tier === "SAFETY").length;
    const offers = applications.filter((a) => a.stage === "offer_received" || a.stage === "offer_accepted").length;
    return { total, dream, target, safety, offers };
  }, [applications]);

  // Active checklist details
  const activeChecklistDetails: DocumentChecklistResult | null = useMemo(() => {
    if (!activeChecklistApp) return null;
    return getLocalDocumentChecklist({
      country_code: activeChecklistApp.country_code,
      degree_level: activeChecklistApp.degree_level,
    });
  }, [activeChecklistApp]);

  return (
    <div className="space-y-8">
      {/* Top Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-[#262846] bg-[#101227]/90 p-6 sm:p-8 backdrop-blur-xl">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-gradient-to-br from-[#FF7A00]/20 to-[#FF4500]/10 blur-3xl" />
        <div className="absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold text-orange-400">
              <LayoutDashboard className="h-3.5 w-3.5" />
              <span>AUSA Tələbə Tətbiq Portalı</span>
            </div>
            <h1 className="mt-3 text-3xl sm:text-4xl font-black tracking-tight text-white">
              Tələbə Müraciət İdarəetmə Paneli
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-300 max-w-2xl">
              Xəyal, hədəf və təhlükəsiz universitet seçimlərinizi izləyin, sənəd yoxlama siyahılarını tamamlayın və qəbul şansınızı sistemli şəkildə artırın.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setShowComparisonModal(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-2.5 text-sm font-semibold text-blue-300 hover:bg-blue-500/20 transition shadow-lg shadow-blue-500/5"
            >
              <Scale className="h-4 w-4" />
              <span>Universitetləri Müqayisə Et</span>
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#FF7A00] to-[#FF4500] px-4 py-2.5 text-sm font-semibold text-white hover:opacity-95 transition shadow-lg shadow-orange-500/20"
            >
              <Plus className="h-4 w-4" />
              <span>Yeni Müraciət Əlavə Et</span>
            </button>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="relative z-10 mt-8 grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4">
          <div className="rounded-2xl border border-[#262846] bg-[#141733]/60 p-4">
            <p className="text-xs uppercase tracking-wider text-slate-400">Cəmi Müraciətlər</p>
            <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
          </div>
          <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
            <p className="text-xs uppercase tracking-wider text-purple-400">Dream (Xəyal)</p>
            <p className="text-2xl font-bold text-purple-300 mt-1">{stats.dream}</p>
          </div>
          <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-4">
            <p className="text-xs uppercase tracking-wider text-blue-400">Target (Hədəf)</p>
            <p className="text-2xl font-bold text-blue-300 mt-1">{stats.target}</p>
          </div>
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <p className="text-xs uppercase tracking-wider text-emerald-400">Safety (Təhlükəsiz)</p>
            <p className="text-2xl font-bold text-emerald-300 mt-1">{stats.safety}</p>
          </div>
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 col-span-2 sm:col-span-1">
            <p className="text-xs uppercase tracking-wider text-amber-400">Qəbullar</p>
            <p className="text-2xl font-bold text-amber-300 mt-1">{stats.offers}</p>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#262846] pb-4">
        <div className="flex items-center gap-2">
          {["ALL", "DREAM", "TARGET", "SAFETY"].map((tier) => (
            <button
              key={tier}
              onClick={() => setTierFilter(tier)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                tierFilter === tier
                  ? "bg-gradient-to-r from-[#FF7A00] to-[#FF4500] text-white shadow-md shadow-orange-500/20"
                  : "bg-[#141733]/60 text-slate-400 hover:text-white hover:bg-[#1a1e42]"
              }`}
            >
              {tier === "ALL"
                ? `Hamısı (${stats.total})`
                : tier === "DREAM"
                ? `Dream (${stats.dream})`
                : tier === "TARGET"
                ? `Target (${stats.target})`
                : `Safety (${stats.safety})`}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-400">
          Göstərilir: <span className="font-bold text-white">{filteredApps.length}</span> müraciət
        </div>
      </div>

      {/* Applications Grid */}
      {filteredApps.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[#262846] bg-[#101227]/40 p-12 text-center">
          <GraduationCap className="h-12 w-12 text-slate-500 mb-3" />
          <h3 className="text-lg font-semibold text-white">Bu kateqoriyada müraciət tapılmadı</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm">
            Yeni bir universitet və ya proqram əlavə edərək müraciətlərinizi planlaşdırmağa başlayın.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#FF7A00] to-[#FF4500] px-4 py-2 text-xs font-semibold text-white shadow-md"
          >
            <Plus className="h-4 w-4" />
            <span>Müraciət Əlavə Et</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredApps.map((app) => {
            const tierStyle = TIER_CONFIG[app.tier];
            const completedCount = app.completed_doc_ids?.length || 0;
            const totalDocs = 6;
            const progress = Math.min(100, Math.round((completedCount / totalDocs) * 100));

            return (
              <div
                key={app.id}
                className="group relative flex flex-col justify-between rounded-3xl border border-[#262846] bg-[#12142d]/80 p-6 backdrop-blur-md transition-all hover:border-[#3d4170] hover:shadow-xl hover:shadow-orange-500/5"
              >
                {/* Card Top */}
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${tierStyle.border} ${tierStyle.bg} ${tierStyle.text}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${tierStyle.dot}`} />
                      <span>{tierStyle.label}</span>
                    </span>

                    <button
                      onClick={() => handleDeleteApp(app.id)}
                      className="rounded-lg p-1.5 text-slate-500 hover:bg-red-500/10 hover:text-red-400 transition"
                      title="Müraciəti sil"
                      aria-label="Müraciəti sil"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  <h3 className="text-lg font-bold text-white leading-tight">
                    {app.flag} {app.university_name}
                  </h3>
                  <p className="text-sm font-medium text-orange-400 mt-1">
                    {app.program_name}
                  </p>

                  <div className="mt-3 flex items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Globe2 className="h-3.5 w-3.5 text-slate-500" />
                      <span>
                        {app.city}, {app.country_name}
                      </span>
                    </span>
                  </div>

                  {/* Stage Dropdown */}
                  <div className="mt-4">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Cari Mərhələ
                    </label>
                    <select
                      value={app.stage}
                      onChange={(e) =>
                        handleStageChange(app.id, e.target.value as ApplicationStage)
                      }
                      className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3 py-2 text-xs font-semibold text-slate-200 focus:border-orange-500 focus:outline-none"
                    >
                      {Object.entries(STAGE_LABELS).map(([k, label]) => (
                        <option key={k} value={k}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Document Progress Bar */}
                  <div className="mt-4 rounded-xl border border-[#262846] bg-[#0c0d1b]/60 p-3">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-slate-400">Sənəd Hazırlığı</span>
                      <span className="font-bold text-white">
                        {completedCount} sənəd ({progress}%)
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[#1c2045]">
                      <div
                        className={`h-full transition-all duration-500 ${
                          progress === 100
                            ? "bg-emerald-400"
                            : "bg-gradient-to-r from-[#FF7A00] to-[#FF4500]"
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Card Bottom Actions */}
                <div className="mt-6 pt-4 border-t border-[#262846] flex items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Calendar className="h-3.5 w-3.5 text-slate-500" />
                    <span>Dedlayn: {app.deadline || "2026-07-15"}</span>
                  </div>

                  <button
                    onClick={() => setActiveChecklistApp(app)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-orange-500/30 bg-orange-500/10 px-3 py-1.5 text-xs font-semibold text-orange-400 hover:bg-orange-500/20 transition"
                  >
                    <FileCheck className="h-3.5 w-3.5" />
                    <span>Sənədlər</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Document Checklist Modal */}
      {activeChecklistApp && activeChecklistDetails && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="checklist-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/80 backdrop-blur-md p-4 sm:p-6"
        >
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl border border-[#262846] bg-[#0f1123] shadow-2xl p-6 sm:p-8 text-white">
            <div className="flex items-start justify-between border-b border-[#262846] pb-4 mb-5">
              <div>
                <div className="inline-flex items-center gap-1.5 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-0.5 text-xs font-semibold text-orange-400">
                  <FileCheck className="h-3.5 w-3.5" />
                  <span>Sənəd Yoxlama Siyahısı</span>
                </div>
                <h3 id="checklist-modal-title" className="text-xl sm:text-2xl font-bold text-white mt-1">
                  {activeChecklistApp.university_name} — Tələb Olunan Sənədlər
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ölkə: {activeChecklistDetails.country_name} | Məcbur sənədlər: {activeChecklistDetails.mandatory_count} / {activeChecklistDetails.total_documents}
                </p>
              </div>

              <button
                onClick={() => setActiveChecklistApp(null)}
                className="rounded-full p-2 text-slate-400 hover:bg-[#1a1d36] hover:text-white transition"
                aria-label="Modalı bağla"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Checklist Progress */}
            <div className="mb-6 rounded-2xl border border-[#262846] bg-[#141733] p-4">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="font-semibold text-slate-300">Ümumi İcra Vəziyyəti</span>
                <span className="font-bold text-orange-400">
                  {activeChecklistApp.completed_doc_ids?.length || 0} / {activeChecklistDetails.total_documents} sənəd hazır
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-[#0c0d1b] overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#FF7A00] to-[#FF4500] transition-all duration-300"
                  style={{
                    width: `${
                      Math.round(
                        ((activeChecklistApp.completed_doc_ids?.length || 0) /
                          (activeChecklistDetails.total_documents || 1)) *
                          100
                      )
                    }%`,
                  }}
                />
              </div>
            </div>

            {/* Document Items List */}
            <div className="space-y-3">
              {activeChecklistDetails.documents.map((doc) => {
                const isCompleted =
                  activeChecklistApp.completed_doc_ids?.includes(doc.id) || false;

                return (
                  <div
                    key={doc.id}
                    onClick={() => handleToggleDocument(activeChecklistApp.id, doc.id)}
                    className={`flex items-start gap-3.5 rounded-2xl border p-4 cursor-pointer transition ${
                      isCompleted
                        ? "border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500/50"
                        : "border-[#262846] bg-[#13152c]/60 hover:border-[#3b3f6d]"
                    }`}
                  >
                    <button
                      type="button"
                      className="mt-0.5 text-slate-400 hover:text-white"
                      aria-label={`Toggle ${doc.title}`}
                    >
                      {isCompleted ? (
                        <CheckSquare className="h-5 w-5 text-emerald-400" />
                      ) : (
                        <Square className="h-5 w-5 text-slate-500" />
                      )}
                    </button>

                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-sm font-semibold ${
                            isCompleted ? "line-through text-slate-400" : "text-white"
                          }`}
                        >
                          {doc.title}
                        </span>
                        {doc.is_mandatory && (
                          <span className="rounded bg-red-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-red-400 border border-red-500/20">
                            Mütləq
                          </span>
                        )}
                        {doc.translation_required && (
                          <span className="rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-blue-400 border border-blue-500/20">
                            Tərcümə
                          </span>
                        )}
                        {doc.apostille_required && (
                          <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-amber-400 border border-amber-500/20">
                            Apostil
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{doc.description}</p>
                      <div className="mt-2 flex items-center gap-4 text-[11px] text-slate-500">
                        <span>Verən orqan: {doc.issuing_authority}</span>
                        <span>İcra müddəti: ~{doc.estimated_processing_days} gün</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setActiveChecklistApp(null)}
                className="rounded-xl bg-gradient-to-r from-[#FF7A00] to-[#FF4500] px-6 py-2.5 text-xs font-semibold text-white shadow-md hover:opacity-95 transition"
              >
                Yadda Saxla & Bağla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add New Application Modal */}
      {showAddModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/80 backdrop-blur-md p-4 sm:p-6"
        >
          <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-3xl border border-[#262846] bg-[#0f1123] shadow-2xl p-6 sm:p-8 text-white">
            <div className="flex items-start justify-between border-b border-[#262846] pb-4 mb-5">
              <div>
                <h3 id="add-modal-title" className="text-xl font-bold text-white">
                  Yeni Universitet Müraciəti Əlavə Et
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Kataloqdakı hazır benchmark universitetlərdən seçin və ya fərdi proqram daxil edin.
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-[#1a1d36] hover:text-white transition"
                aria-label="Modalı bağla"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddApplication} className="space-y-4">
              {/* Benchmark Selector */}
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Hazır Benchmark Universitetlər
                </label>
                <select
                  aria-label="Hazır Benchmark Universitetlər"
                  value={selectedBenchmark}
                  onChange={(e) => {
                    setSelectedBenchmark(e.target.value);
                    if (e.target.value && CURATED_BENCHMARKS[e.target.value]) {
                      const b = CURATED_BENCHMARKS[e.target.value];
                      setCustomUniName(b.university_name);
                      setCustomProgram(b.program_name);
                      setCustomCountry(b.country_code);
                      setCustomCity(b.city);
                      setCustomTier(b.admission_tier);
                    }
                  }}
                  className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2.5 text-xs text-slate-200 focus:border-orange-500 focus:outline-none"
                >
                  <option value="">Fərdi daxil etmə (Kataloqdan kənar)</option>
                  {Object.values(CURATED_BENCHMARKS).map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.flag} {b.university_name} — {b.program_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Custom University and Program */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Universitet Adı
                  </label>
                  <input
                    type="text"
                    required
                    value={customUniName}
                    onChange={(e) => setCustomUniName(e.target.value)}
                    placeholder="Məs. Technical University of Munich"
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    İxtisas / Proqram
                  </label>
                  <input
                    type="text"
                    required
                    value={customProgram}
                    onChange={(e) => setCustomProgram(e.target.value)}
                    placeholder="Məs. MSc Informatics"
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Country and City */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Ölkə</label>
                  <select
                    value={customCountry}
                    onChange={(e) => setCustomCountry(e.target.value)}
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-slate-200 focus:border-orange-500 focus:outline-none"
                  >
                    <option value="DE">Almaniya (DE)</option>
                    <option value="GB">Böyük Britaniya (GB)</option>
                    <option value="IT">İtaliya (IT)</option>
                    <option value="TR">Türkiyə (TR)</option>
                    <option value="US">ABŞ (US)</option>
                    <option value="AZ">Azərbaycan (AZ)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Şəhər</label>
                  <input
                    type="text"
                    value={customCity}
                    onChange={(e) => setCustomCity(e.target.value)}
                    placeholder="Münhen, London və s."
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Tier and Deadline */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Müraciət Kateqoriyası (Tier)
                  </label>
                  <select
                    value={customTier}
                    onChange={(e) => setCustomTier(e.target.value as AdmissionTier)}
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-slate-200 focus:border-orange-500 focus:outline-none"
                  >
                    <option value="DREAM">DREAM (Xəyal / Yüksək Rəqabət)</option>
                    <option value="TARGET">TARGET (Hədəf / Real Uyğunluq)</option>
                    <option value="SAFETY">SAFETY (Təhlükəsiz / Zəmanətli)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Son Müraciət Tarixi
                  </label>
                  <input
                    type="date"
                    value={customDeadline}
                    onChange={(e) => setCustomDeadline(e.target.value)}
                    className="w-full rounded-xl border border-[#2c3058] bg-[#0c0d1b] px-3.5 py-2 text-xs text-white focus:border-orange-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-[#262846]">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded-xl border border-[#3b3e66] bg-[#1a1d38] px-4 py-2 text-xs font-semibold text-white hover:bg-[#25284e] transition"
                >
                  Ləğv Et
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-gradient-to-r from-[#FF7A00] to-[#FF4500] px-5 py-2 text-xs font-semibold text-white shadow-md hover:opacity-95 transition"
                >
                  Müraciəti Əlavə Et
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Comparison Matrix Modal */}
      {showComparisonModal && (
        <ComparisonMatrix
          isOpen={showComparisonModal}
          onClose={() => setShowComparisonModal(false)}
        />
      )}
    </div>
  );
}
