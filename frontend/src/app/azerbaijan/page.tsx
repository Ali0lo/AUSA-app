"use client";

import { useEffect, useState } from "react";
import { getAzerbaijanPredictions, type AzerbaijanPrediction, ApiError } from "@/lib/api";
import { ScrollReveal } from "@/components/ScrollReveal";
import { DEMO_AZERBAIJAN } from "@/lib/demoExamples";
import { useLanguage } from "@/lib/i18n";

function verdict(row: AzerbaijanPrediction, score: number | null) {
  if (score === null) return null;
  const cutoff = row.predicted_cutoff ?? 650;
  const lower = row.lower_cutoff ?? 650;
  const upper = row.upper_cutoff ?? 700;
  if (score >= upper) return "clears";
  if (score >= cutoff) return "clears cutoff";
  if (score < lower) return "below";
  return "close";
}

export default function AzerbaijanPage() {
  const { language } = useLanguage();
  const [university, setUniversity] = useState("");
  const [group, setGroup] = useState("");
  const [score, setScore] = useState("");
  const [rows, setRows] = useState<AzerbaijanPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const scoreValue = score === "" ? null : Number(score);

  const copy = language === "ru"
    ? {
        eyebrow: "Азербайджан · DİM",
        title: "Каким может быть следующий проходной балл?",
        intro: "Прогноз опубликованных проходных баллов DİM для государственных программ азербайджанских университетов на основе истории поступления.",
        filter: "Фильтр прогнозов Азербайджана",
        university: "Университет",
        group: "Группа DİM",
        allGroups: "Все группы",
        allUnis: "Все университеты",
        score: "Ваш балл DİM (необязательно)",
        search: "Поиск университета",
        noResults: "Нет прогнозов, соответствующих вашему поиску.",
        scholarship: "Полная стипендия (Госзаказ)",
        bandHelp: "Диапазон отражает интервал устойчивости и неопределённости. «Проходит» означает, что ваш балл превышает прогнозируемый порог.",
        clears: "проходит",
        clearsCutoff: "проходит по баллу",
        close: "на грани прохождения",
        below: "ниже проходного балла",
        cutoffLabel: "Проходной балл (Госзаказ)",
        bandLabel: "Диапазон",
        projectionYear: "Год прогноза",
        upcomingIntake: "Ближайший приём",
        methodology: "Методология",
        historicalData: "Исторические данные",
        yearsHistory: "лет приёма",
        officialStandard: "Официальный стандарт",
        group1: "1-я группа",
        group2: "2-я группа",
        group3: "3-я группа",
        group4: "4-я группа",
        group5: "5-я группа",
        demo: "Демо-пример"
      }
    : language === "az"
      ? {
          eyebrow: "Azərbaycan · DİM",
          title: "Növbəti keçid balı nə qədər ola bilər?",
          intro: "Azərbaycan universitetlərində dövlət sifarişli proqramlar üçün DİM keçid ballarını qəbul tarixçəsinə əsasən proqnozlaşdırır.",
          filter: "Azərbaycan proqnozlarını filtrlə",
          university: "Universitet",
          group: "DİM qrupu",
          allGroups: "Bütün qruplar",
          allUnis: "Bütün universitetlər",
          score: "DİM balınız (istəyə bağlı)",
          search: "Universitet axtar",
          noResults: "Axtarışınıza uyğun proqnoz tapılmadı.",
          scholarship: "Tam təqaüd (Dövlət sifarişi)",
          bandHelp: "Diapazon dayanıqlıq və qeyri-müəyyənlik intervalını əks etdirir. «Keçir» balınızın proqnozlaşdırılan keçid diapazonunu aşdığını bildirir.",
          clears: "keçir",
          clearsCutoff: "keçid balını keçir",
          close: "sərhədə çox yaxındır",
          below: "keçid balından aşağı",
          cutoffLabel: "Keçid balı (Dövlət sifarişi)",
          bandLabel: "Diapazon",
          projectionYear: "Proqnoz ili",
          upcomingIntake: "Növbəti qəbul",
          methodology: "Metodologiya",
          historicalData: "Tarixi məlumatlar",
          yearsHistory: "il qəbul tarixi",
          officialStandard: "Rəsmi standart",
          group1: "I qrup",
          group2: "II qrup",
          group3: "III qrup",
          group4: "IV qrup",
          group5: "V qrup",
          demo: "Demo nümunəsi"
        }
      : {
          eyebrow: "Azerbaijan · DİM Admissions",
          title: "What may the next cutoff be?",
          intro: "Predicts published DİM cutoffs for state-funded programmes at Azerbaijani universities from official cutoff history.",
          filter: "Filter Azerbaijan predictions",
          university: "University",
          group: "DİM group",
          allGroups: "All groups",
          allUnis: "All Universities",
          score: "Your DİM score (optional)",
          search: "Search a university",
          noResults: "No Azerbaijan cutoff predictions are available matching your search.",
          scholarship: "Full Scholarship",
          bandHelp: "The band reflects the persistence and uncertainty interval. “Clears” means your score exceeds the projected cutoff range.",
          clears: "clears",
          clearsCutoff: "clears cutoff",
          close: "too close to call",
          below: "below",
          cutoffLabel: "Cutoff Score (Full Scholarship)",
          bandLabel: "Band",
          projectionYear: "Projection Year",
          upcomingIntake: "Upcoming intake",
          methodology: "Methodology",
          historicalData: "Historical Data",
          yearsHistory: "intake years",
          officialStandard: "Official standard",
          group1: "Group 1",
          group2: "Group 2",
          group3: "Group 3",
          group4: "Group 4",
          group5: "Group 5",
          demo: "Try demo example"
        };

  const POPULAR_UNIVERSITIES = [
    { label: copy.allUnis, value: "" },
    { label: "Baku Higher Oil School (BHOS)", value: "bhos" },
    { label: "ADA University", value: "ada" },
    { label: "UNEC", value: "unec" },
    { label: "BDU", value: "bdu" },
  ];

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      getAzerbaijanPredictions({ university, group })
        .then((result) => {
          setRows(result.items);
          setError(null);
        })
        .catch((reason) => {
          setError(reason instanceof ApiError ? reason.message : "The Azerbaijan cutoff service is unavailable.");
        })
        .finally(() => setLoading(false));
    }, 200);
    return () => window.clearTimeout(timer);
  }, [university, group]);

  return (
    <div className="app-page">
      <ScrollReveal direction="down" duration={600}>
        <div className="flex flex-col gap-4 border-b border-white/[0.08] pb-8 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3.5 py-1 text-xs font-semibold text-orange-400 backdrop-blur-md">
              <span className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-pulse" />
              {copy.eyebrow}
            </span>
            <h1 className="mt-4 font-sans text-3xl font-extrabold tracking-tight text-white md:text-5xl">
              {copy.title}
            </h1>
            <p className="mt-3 text-base leading-relaxed text-slate-300">
              {copy.intro}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-medium text-slate-300 backdrop-blur-md">
              Model: Persistence + Band
            </span>
            <span className="rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-medium text-slate-300 backdrop-blur-md">
              2026 Projections
            </span>
          </div>
        </div>
      </ScrollReveal>

      <ScrollReveal direction="up" delay={150} duration={600}>
        <section className="panel mt-8 p-6" aria-label={copy.filter}>
          <div className="mb-6 flex flex-wrap gap-2">
            {POPULAR_UNIVERSITIES.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setUniversity(item.value)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-all ${
                  university === item.value
                    ? "bg-gradient-to-r from-orange-500 to-purple-600 font-semibold text-white shadow-md shadow-orange-500/20"
                    : "border border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10"
                }`}
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => {
                setUniversity(DEMO_AZERBAIJAN.university);
                setGroup(DEMO_AZERBAIJAN.group);
                setScore(DEMO_AZERBAIJAN.score);
              }}
              className="rounded-full border border-dashed border-orange-500/40 px-3.5 py-1.5 text-xs font-medium text-orange-300 transition-all hover:bg-orange-500/10"
            >
              {copy.demo}
            </button>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            <label>
              <span className="field-label">{copy.university}</span>
              <input
                className="field"
                value={university}
                onChange={(event) => setUniversity(event.target.value)}
                placeholder={`${copy.search} (e.g. Baku Higher Oil School, ADA)`}
              />
            </label>
            <label>
              <span className="field-label">{copy.group}</span>
              <select className="field" value={group} onChange={(event) => setGroup(event.target.value)}>
                <option value="">{copy.allGroups}</option>
                <option value="I qrup">{copy.group1}</option>
                <option value="II qrup">{copy.group2}</option>
                <option value="III qrup">{copy.group3}</option>
                <option value="IV qrup">{copy.group4}</option>
                <option value="V qrup">{copy.group5}</option>
              </select>
            </label>
            <label>
              <span className="field-label">{copy.score}</span>
              <input
                className="field"
                type="number"
                min="0"
                max="700"
                value={score}
                onChange={(event) => setScore(event.target.value)}
                placeholder="0–700"
              />
            </label>
          </div>
          <p className="field-help mt-4">
            {copy.bandHelp}
          </p>
        </section>
      </ScrollReveal>

      {error && <p className="notice notice-warning mt-8" role="alert">{error}</p>}

      {!error && !loading && rows.length === 0 && (
        <p className="notice notice-info mt-8">
          {copy.noResults} Try searching for “Baku Higher Oil School”, “BHOS”, or “ADA”.
        </p>
      )}

      <div className="mt-8 grid gap-4">
        {rows.map((row, idx) => {
          const state = verdict(row, Number.isFinite(scoreValue) ? scoreValue : null);
          const isBHOS = row.university_name?.toLowerCase().includes("oil") || row.university_name?.toLowerCase().includes("banm");
          const cutoffDisplay = row.predicted_cutoff != null
            ? `${row.predicted_cutoff.toFixed(1)} pts`
            : "650+ pts (Standard full scholarship)";

          const stateLabel = state === "clears cutoff"
            ? copy.clearsCutoff
            : state === "clears"
            ? copy.clears
            : state === "close"
            ? copy.close
            : state === "below"
            ? copy.below
            : state;

          return (
            <ScrollReveal key={row.program_code || idx} direction="up" delay={Math.min(idx * 40, 300)} duration={500}>
              <article className={`panel p-5 sm:p-6 transition-all hover:border-purple-500/40 ${isBHOS ? "border-purple-500/30 bg-white/[0.06]" : ""}`}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-serif text-2xl font-semibold text-white">
                        {row.department_name || "Unnamed programme"}
                      </h2>
                      <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-300">
                        {row.scholarship_type || copy.scholarship}
                      </span>
                    </div>
                    <p className="mt-1 text-muted">
                      <span className="font-medium text-slate-200">{row.university_name}</span> · {row.score_type || "DİM score"}
                    </p>
                  </div>
                  {state && (
                    <span
                      className={`status-tag ${
                        state === "clears" || state === "clears cutoff"
                          ? "status-available"
                          : state === "below"
                          ? "status-offline"
                          : "status-experimental"
                      }`}
                    >
                      {stateLabel}
                    </span>
                  )}
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-4 border-t border-white/5 pt-4">
                  <div>
                    <p className="eyebrow">{copy.cutoffLabel}</p>
                    <p className="mt-1 text-2xl font-bold bg-gradient-to-r from-purple-200 via-pink-200 to-orange-200 bg-clip-text text-transparent">
                      {cutoffDisplay}
                    </p>
                    {row.lower_cutoff != null && row.upper_cutoff != null && (
                      <p className="mt-0.5 text-xs text-slate-400">
                        {copy.bandLabel}: {row.lower_cutoff.toFixed(0)}–{row.upper_cutoff.toFixed(0)}
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="eyebrow">{copy.projectionYear}</p>
                    <p className="mt-1 font-medium text-slate-200">{row.target_year || 2026}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{copy.upcomingIntake}</p>
                  </div>
                  <div>
                    <p className="eyebrow">{copy.methodology}</p>
                    <p className="mt-1 font-medium text-slate-200">{row.model || "Persistence"}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{row.prediction_type || "forecast"}</p>
                  </div>
                  <div>
                    <p className="eyebrow">{copy.historicalData}</p>
                    <p className="mt-1 font-medium text-slate-200">
                      {row.history_years ? `${row.history_years} ${copy.yearsHistory}` : copy.officialStandard}
                    </p>
                    <p className="mt-0.5 text-xs text-purple-300/80">
                      {row.cutoff_note || "Full scholarship standard (650+)"}
                    </p>
                  </div>
                </div>
              </article>
            </ScrollReveal>
          );
        })}
      </div>
    </div>
  );
}