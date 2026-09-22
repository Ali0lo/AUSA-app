"use client";

import React, { useState, useMemo } from "react";
import {
  UniversityComparisonItem,
  ComparisonResult,
  CURATED_BENCHMARKS,
  getLocalComparison,
} from "@/lib/application-tracker-api";
import {
  X,
  TrendingDown,
  Clock,
  Award,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface ComparisonMatrixProps {
  initialUniversityIds?: string[];
  isOpen?: boolean;
  onClose?: () => void;
}

export function ComparisonMatrix({
  initialUniversityIds = ["tum_cs", "oxford_cs", "rwth_engineering"],
  isOpen = true,
  onClose,
}: ComparisonMatrixProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>(initialUniversityIds);
  const [showAddSelector, setShowAddSelector] = useState(false);

  // Compute comparison synchronously to avoid async hydration / test timing lag
  const comparison: ComparisonResult = useMemo(() => {
    return getLocalComparison({ university_ids: selectedIds });
  }, [selectedIds]);

  const handleRemove = (idToRemove: string) => {
    setSelectedIds((prev) => prev.filter((id) => id !== idToRemove));
  };

  const handleAdd = (idToAdd: string) => {
    if (!selectedIds.includes(idToAdd) && selectedIds.length < 5) {
      setSelectedIds((prev) => [...prev, idToAdd]);
    }
    setShowAddSelector(false);
  };

  const availableToAdd = Object.values(CURATED_BENCHMARKS).filter(
    (b) => !selectedIds.includes(b.id)
  );

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="comparison-matrix-title"
      className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/80 backdrop-blur-md p-4 sm:p-6"
    >
      <div className="relative w-full max-w-6xl max-h-[92vh] overflow-y-auto rounded-3xl border border-[#262846] bg-[#0f1123] shadow-2xl p-6 sm:p-8 text-white">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#262846] pb-6 mb-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold text-orange-400">
              <Award className="h-3.5 w-3.5" />
              <span>Çoxölçülü Müqayisə Matrisi</span>
            </div>
            <h2
              id="comparison-matrix-title"
              className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-white"
            >
              Universitetlərin Müqayisəsi & Xərc/Viza Təhlili
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Təhsil haqları, rəsmi bloklanmış hesablar, yaşayış xərcləri və məzuniyyət iş vizası imkanlarını yan-yana müqayisə edin.
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-full p-2 text-slate-400 hover:bg-[#1a1d36] hover:text-white transition-colors"
              aria-label="Bağla"
            >
              <X className="h-6 w-6" />
            </button>
          )}
        </div>

        {/* Highlight Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="flex items-center gap-3.5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <TrendingDown className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-400">Ən Sərfəli Seçim</p>
              <p className="font-semibold text-white text-sm truncate">
                {comparison.lowest_cost_university || "Məlumat yoxdur"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3.5 rounded-2xl border border-blue-500/20 bg-blue-500/5 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-400">Ən Uzun İş Vizası</p>
              <p className="font-semibold text-white text-sm truncate">
                {comparison.longest_pswr_university || "Məlumat yoxdur"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3.5 rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-400">Top Reytinqli Universitet</p>
              <p className="font-semibold text-white text-sm truncate">
                {comparison.best_ranked_university || "Məlumat yoxdur"}
              </p>
            </div>
          </div>
        </div>

        {/* Add University Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 bg-[#13162d] border border-[#262846] p-4 rounded-2xl">
          <div className="text-sm text-slate-300">
            Müqayisədə olan universitetlər:{" "}
            <span className="font-bold text-white">{comparison.items.length} / 5</span>
          </div>
          {comparison.items.length < 5 && availableToAdd.length > 0 && (
            <div className="relative">
              {!showAddSelector ? (
                <button
                  onClick={() => setShowAddSelector(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#FF7A00] to-[#FF4500] px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-orange-500/20 hover:opacity-95 transition"
                >
                  <Plus className="h-4 w-4" />
                  <span>Universitet Əlavə Et</span>
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <select
                    onChange={(e) => {
                      if (e.target.value) handleAdd(e.target.value);
                    }}
                    defaultValue=""
                    className="rounded-xl border border-[#3b3e66] bg-[#0c0d1b] px-3 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                    aria-label="Universitet seçimi"
                  >
                    <option value="" disabled>
                      Müqayisəyə universitet seç...
                    </option>
                    {availableToAdd.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.university_name} ({b.country_code})
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => setShowAddSelector(false)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white"
                    aria-label="Ləğv et"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto rounded-2xl border border-[#262846] bg-[#13152c]/50">
          <table className="w-full text-left text-sm text-slate-300 border-collapse">
            <thead>
              <tr className="border-b border-[#262846] bg-[#1a1d38]">
                <th className="p-4 font-semibold text-slate-200 min-w-[200px]">Meyarlar</th>
                {comparison.items.map((item) => (
                  <th key={item.id} className="p-4 font-semibold text-white min-w-[220px]">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <span className="text-base font-bold text-white block">
                          {item.flag} {item.university_name}
                        </span>
                        <span className="text-xs text-slate-400">
                          {item.city}, {item.country_name}
                        </span>
                      </div>
                      {comparison.items.length > 1 && (
                        <button
                          onClick={() => handleRemove(item.id)}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition"
                          title="Müqayisədən çıxar"
                          aria-label={`${item.university_name} sil`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#262846]/60">
              {/* Proqram */}
              <tr>
                <td className="p-4 font-medium text-slate-400">İxtisas / Proqram</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4 text-white font-medium">
                    {item.program_name} ({item.degree_level.toUpperCase()})
                  </td>
                ))}
              </tr>

              {/* QS Reytinqi */}
              <tr>
                <td className="p-4 font-medium text-slate-400">QS Dünya Reytinqi</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4">
                    {item.qs_rank ? (
                      <span className="inline-flex items-center gap-1 font-semibold text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full text-xs">
                        🏆 Top #{item.qs_rank}
                      </span>
                    ) : (
                      <span className="text-slate-500 text-xs">Reytinq daxilində deyil</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* İllik Təhsil Haqqı */}
              <tr>
                <td className="p-4 font-medium text-slate-400">İllik Təhsil Haqqı (€)</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4 font-semibold text-white">
                    {item.tuition_eur_annual === 0 ? (
                      <span className="text-emerald-400 font-bold">Pulsuz (€0/il)</span>
                    ) : (
                      `€${item.tuition_eur_annual.toLocaleString()}`
                    )}
                    <span className="block text-[11px] text-slate-400 font-normal mt-0.5">
                      {item.original_tuition}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Aylıq Yaşayış Xərci */}
              <tr>
                <td className="p-4 font-medium text-slate-400">Aylıq Yaşayış Xərci</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4">
                    €{item.living_cost_eur_monthly.toLocaleString()} / ay
                  </td>
                ))}
              </tr>

              {/* Viza / Bloklanmış Hesab */}
              <tr>
                <td className="p-4 font-medium text-slate-400">Bloklanmış Hesab / Viza Tələbi</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4 text-orange-400 font-semibold">
                    {item.blocked_account_required_eur > 0
                      ? `€${item.blocked_account_required_eur.toLocaleString()}`
                      : "Tələb olunmur"}
                  </td>
                ))}
              </tr>

              {/* İlk İl Təxmini Cəmi Xərc */}
              <tr className="bg-orange-500/5">
                <td className="p-4 font-bold text-orange-400">İlk İl Təxmini Cəmi Xərc</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4 font-bold text-white text-base">
                    €{item.total_first_year_eur.toLocaleString()}
                  </td>
                ))}
              </tr>

              {/* Post-Study Work Visa */}
              <tr>
                <td className="p-4 font-medium text-slate-400">Məzuniyyət İş Vizası (PSWR)</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4">
                    <div className="font-semibold text-emerald-400">
                      {item.post_study_work_visa_duration_months} ay ({Math.round(item.post_study_work_visa_duration_months / 12)} il)
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">{item.post_study_work_visa_name}</div>
                  </td>
                ))}
              </tr>

              {/* Minimum Dil Nəticəsi */}
              <tr>
                <td className="p-4 font-medium text-slate-400">Minimum Dil Tələbi</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4 font-semibold text-white">
                    IELTS {item.ielts_min} / TOEFL {item.toefl_min}
                  </td>
                ))}
              </tr>

              {/* Dövlət Proqramı Təsdiqi */}
              <tr>
                <td className="p-4 font-medium text-slate-400">Dövlət Proqramı Uyğunluğu</td>
                {comparison.items.map((item) => (
                  <td key={item.id} className="p-4">
                    {item.state_programme_eligible ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Dövlət Proqramı Təsdiqli</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800/40 px-2.5 py-1 rounded-full border border-slate-700">
                        <AlertCircle className="h-3.5 w-3.5" />
                        <span>Fərdi / Universitet Qrantı</span>
                      </span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Summary Insights */}
        <div className="mt-6 rounded-2xl border border-[#262846] bg-[#13162d] p-5">
          <h4 className="text-xs uppercase tracking-wider font-bold text-orange-400 mb-2">
            Ekspert Müqayisə Qeydləri
          </h4>
          <ul className="space-y-1.5 text-sm text-slate-300">
            {comparison.comparison_summary_notes.map((note, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Close button at bottom */}
        {onClose && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="rounded-xl border border-[#3b3e66] bg-[#1a1d38] px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#25284e] transition"
            >
              Bağla
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
