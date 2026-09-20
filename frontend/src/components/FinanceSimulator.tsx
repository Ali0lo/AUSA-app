"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Currency,
  GermanCityTier,
  UKLocationType,
  USLivingLocationTier,
  ItalyCityTier,
  GermanyProofOfFundsResponse,
  UKProofOfFundsResponse,
  USProofOfFundsResponse,
  ItalyProofOfFundsResponse,
  DestinationCompareResponse,
  calculateGermanyLocal,
  calculateUKLocal,
  calculateUSLocal,
  calculateItalyLocal,
  compareDestinationsLocal,
  FALLBACK_RATES_TO_AZN,
} from "@/lib/finance-api";
import {
  Coins,
  Building2,
  Landmark,
  PiggyBank,
  CheckCircle2,
  AlertTriangle,
  Info,
  ArrowRightLeft,
  Copy,
  Check,
  ShieldCheck,
  Sliders,
  DollarSign,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

type ActiveTab = "germany" | "uk" | "usa" | "italy" | "compare" | "converter";

export function FinanceSimulator() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("germany");
  const [copied, setCopied] = useState(false);

  // -------------------------------------------------------------
  // 1. Germany State
  // -------------------------------------------------------------
  const [deMonths, setDeMonths] = useState(12);
  const [deCityTier, setDeCityTier] = useState<GermanCityTier>("tier_2_moderate");
  const [deTuition, setDeTuition] = useState(0);
  const [deArrivalBuffer, setDeArrivalBuffer] = useState(true);

  const deResult: GermanyProofOfFundsResponse = useMemo(() => {
    return calculateGermanyLocal({
      months: deMonths,
      city_tier: deCityTier,
      tuition_fee_eur: deTuition,
      include_arrival_buffer: deArrivalBuffer,
      exchange_safety_buffer_pct: 3.0,
    });
  }, [deMonths, deCityTier, deTuition, deArrivalBuffer]);

  // -------------------------------------------------------------
  // 2. UK State
  // -------------------------------------------------------------
  const [ukLocation, setUkLocation] = useState<UKLocationType>("outside_london");
  const [ukTuition, setUkTuition] = useState(18500);
  const [ukDeposit, setUkDeposit] = useState(2000);
  const [ukDuration, setUkDuration] = useState(9);

  const ukResult: UKProofOfFundsResponse = useMemo(() => {
    return calculateUKLocal({
      location_type: ukLocation,
      course_tuition_annual_gbp: ukTuition,
      deposit_paid_to_cas_gbp: ukDeposit,
      course_duration_months: ukDuration,
      exchange_safety_buffer_pct: 3.0,
    });
  }, [ukLocation, ukTuition, ukDeposit, ukDuration]);

  // -------------------------------------------------------------
  // 3. USA State
  // -------------------------------------------------------------
  const [usTuition, setUsTuition] = useState(28000);
  const [usFees, setUsFees] = useState(1800);
  const [usLocation, setUsLocation] = useState<USLivingLocationTier>("suburban_moderate");
  const [usScholarship, setUsScholarship] = useState(0);

  const usResult: USProofOfFundsResponse = useMemo(() => {
    return calculateUSLocal({
      tuition_annual_usd: usTuition,
      institutional_fees_usd: usFees,
      location_tier: usLocation,
      scholarship_award_usd: usScholarship,
      exchange_safety_buffer_pct: 3.0,
    });
  }, [usTuition, usFees, usLocation, usScholarship]);

  // -------------------------------------------------------------
  // 4. Italy State
  // -------------------------------------------------------------
  const [itMembers, setItMembers] = useState(4);
  const [itIncomeAzn, setItIncomeAzn] = useState(24000);
  const [itPropertyAzn, setItPropertyAzn] = useState(80000);
  const [itCityTier, setItCityTier] = useState<ItalyCityTier>("tier_2_major_student");
  const [itBaseTuition, setItBaseTuition] = useState(3500);

  const itResult: ItalyProofOfFundsResponse = useMemo(() => {
    return calculateItalyLocal({
      family_members_count: itMembers,
      family_annual_income_azn: itIncomeAzn,
      real_estate_abroad_azn: itPropertyAzn,
      city_tier: itCityTier,
      base_tuition_eur: itBaseTuition,
      exchange_safety_buffer_pct: 3.0,
    });
  }, [itMembers, itIncomeAzn, itPropertyAzn, itCityTier, itBaseTuition]);

  // -------------------------------------------------------------
  // 5. Compare State
  // -------------------------------------------------------------
  const [compareBudgetAzn, setCompareBudgetAzn] = useState(35000);

  const compareResult: DestinationCompareResponse = useMemo(() => {
    return compareDestinationsLocal({
      student_annual_budget_azn: compareBudgetAzn,
      tuition_eur: deTuition,
      tuition_gbp: ukTuition,
      tuition_usd: usTuition,
      tuition_italy_eur: itBaseTuition,
      family_members_count: itMembers,
      family_income_azn: itIncomeAzn,
    });
  }, [compareBudgetAzn, deTuition, ukTuition, usTuition, itBaseTuition, itMembers, itIncomeAzn]);

  // -------------------------------------------------------------
  // 6. Currency Converter State
  // -------------------------------------------------------------
  const [convAmount, setConvAmount] = useState(1000);
  const [fromCurr, setFromCurr] = useState<Currency>("EUR");
  const [toCurr, setToCurr] = useState<Currency>("AZN");

  const convertedResult = useMemo(() => {
    const rateFrom = FALLBACK_RATES_TO_AZN[fromCurr] || 1.0;
    const rateTo = FALLBACK_RATES_TO_AZN[toCurr] || 1.0;
    const rate = rateFrom / rateTo;
    const converted = Math.round(convAmount * rate * 100) / 100;
    const toAzn = convAmount * rateFrom;
    return {
      converted,
      rate: Math.round(rate * 10000) / 10000,
      breakdown: {
        AZN: Math.round(toAzn * 100) / 100,
        EUR: Math.round((toAzn / FALLBACK_RATES_TO_AZN.EUR) * 100) / 100,
        USD: Math.round((toAzn / FALLBACK_RATES_TO_AZN.USD) * 100) / 100,
        GBP: Math.round((toAzn / FALLBACK_RATES_TO_AZN.GBP) * 100) / 100,
      },
    };
  }, [convAmount, fromCurr, toCurr]);

  const copySummary = () => {
    let text = "";
    if (activeTab === "germany") {
      text = `[AUSA Germany Visa Simulation]\nDuration: ${deResult.number_of_months} months\nStatutory Blocked Account Deposit: €${deResult.total_blocked_deposit_required.toLocaleString()}\nTotal First Year Liquidity: €${deResult.total_first_year_liquidity_eur.toLocaleString()} (~${deResult.total_first_year_liquidity_azn.toLocaleString()} AZN)\n${deResult.statutory_note}`;
    } else if (activeTab === "uk") {
      text = `[AUSA UK Student Visa Simulation]\nMaintenance Rate: £${ukResult.maintenance_monthly_rate_gbp}/mo (9 months assessed: £${ukResult.maintenance_total_gbp.toLocaleString()})\nOutstanding Tuition: £${ukResult.outstanding_tuition_gbp.toLocaleString()}\nStrict 28-day Bank Holding: £${ukResult.total_funds_to_hold_28_days_gbp.toLocaleString()} (~${ukResult.total_funds_in_azn.toLocaleString()} AZN)\n${ukResult.holding_rule_statement}`;
    } else if (activeTab === "usa") {
      text = `[AUSA US F-1 Visa Simulation]\nOfficial Form I-20 COA: $${usResult.official_i20_total_usd.toLocaleString()}\nRecommended Consular Liquid Affidavit: $${usResult.total_recommended_affidavit_usd.toLocaleString()} (~${usResult.total_in_azn.toLocaleString()} AZN)\n${usResult.consular_advice}`;
    } else if (activeTab === "italy") {
      text = `[AUSA Italy ISEE-U Simulation]\nCalculated ISEE Parificato: €${itResult.calculated_isee_parificato_eur.toLocaleString()}\nDSU Full Fee Exemption: ${itResult.qualifies_for_dsu_fee_waiver ? "QUALIFIED" : "NOT QUALIFIED"}\nEstimated Regional Cash Stipend: €${itResult.estimated_dsu_cash_stipend_eur.toLocaleString()}/yr\nNet First Year Cost: €${itResult.net_first_year_cost_eur.toLocaleString()} (~${itResult.net_first_year_cost_azn.toLocaleString()} AZN)\n${itResult.dsu_eligibility_verdict}`;
    } else {
      text = `[AUSA Study Abroad Budget Comparison]\nAnnual Budget: ${compareResult.student_budget_azn.toLocaleString()} AZN\n${compareResult.summary_verdict}`;
    }

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full space-y-8 animate-fade-in">
      {/* Top Banner & Title */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.06] via-white/[0.02] to-transparent p-6 sm:p-8 backdrop-blur-2xl">
        <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-orange-400">
              <ShieldCheck className="h-3.5 w-3.5" />
              Statutory Visa & Funds Simulator
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Student Visa, Blocked Account & Living Cost Simulator
            </h1>
            <p className="max-w-2xl text-sm sm:text-base text-slate-300">
              Compute official statutory bank proof-of-funds for Germany (§ 16b Sperrkonto), UK CAS 28-day maintenance,
              US Form I-20 Cost of Attendance, and Italy ISEE-U/DSU regional grants with real-time AZN conversion.
            </p>
          </div>

          <button
            onClick={copySummary}
            className="self-start md:self-center inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.05] px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10 hover:border-white/25 active:scale-95 transition-all shadow-sm"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 text-emerald-400" />
                <span className="text-emerald-300">Copied to clipboard</span>
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 text-slate-400" />
                <span>Copy summary</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 p-1.5 rounded-2xl border border-white/[0.08] bg-[#0c0d1b]/80 backdrop-blur-xl">
        <button
          onClick={() => setActiveTab("germany")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "germany"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <span>🇩🇪</span> Germany Sperrkonto
        </button>

        <button
          onClick={() => setActiveTab("uk")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "uk"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <span>🇬🇧</span> UK CAS Maintenance
        </button>

        <button
          onClick={() => setActiveTab("usa")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "usa"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <span>🇺🇸</span> US Form I-20
        </button>

        <button
          onClick={() => setActiveTab("italy")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "italy"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <span>🇮🇹</span> Italy ISEE-U / DSU
        </button>

        <button
          onClick={() => setActiveTab("compare")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "compare"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <Landmark className="h-4 w-4" /> Compare 4 Countries
        </button>

        <button
          onClick={() => setActiveTab("converter")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
            activeTab === "converter"
              ? "bg-gradient-to-r from-orange-500/20 to-purple-500/20 border border-orange-500/40 text-white shadow-inner"
              : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          <ArrowRightLeft className="h-4 w-4" /> Currency Converter
        </button>
      </div>

      {/* TAB CONTENT */}

      {/* --------------------------------------------------------- */}
      {/* 1. GERMANY SPERRKONTO TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "germany" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Controls */}
          <div className="lg:col-span-5 space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="h-5 w-5 text-orange-400" />
              Germany Parameters (§ 16b)
            </h2>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <label className="text-slate-300 font-medium">Duration (Months)</label>
                  <span className="font-semibold text-white">{deMonths} months</span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="24"
                  value={deMonths}
                  onChange={(e) => setDeMonths(Number(e.target.value))}
                  className="w-full accent-orange-500 cursor-pointer"
                />
                <span className="text-xs text-slate-400">German visa standard is 12 months for 1 academic year.</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">City Living Expense Tier</label>
                <select
                  value={deCityTier}
                  onChange={(e) => setDeCityTier(e.target.value as GermanCityTier)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="tier_1_expensive" className="bg-slate-900 text-white">
                    Tier 1 (Expensive: Munich, Frankfurt, Stuttgart)
                  </option>
                  <option value="tier_2_moderate" className="bg-slate-900 text-white">
                    Tier 2 (Moderate: Berlin, Hamburg, Cologne, Aachen)
                  </option>
                  <option value="tier_3_affordable" className="bg-slate-900 text-white">
                    Tier 3 (Affordable: Leipzig, Dresden, Clausthal, Ilmenau)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Annual Tuition Fee (€)
                </label>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={deTuition}
                  onChange={(e) => setDeTuition(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="0 (Public universities charge €0 tuition)"
                />
                <span className="text-xs text-slate-400">Public German universities have €0 tuition (except BW: €1,500/sem).</span>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="de-arrival"
                  checked={deArrivalBuffer}
                  onChange={(e) => setDeArrivalBuffer(e.target.checked)}
                  className="h-4 w-4 rounded accent-orange-500 cursor-pointer"
                />
                <label htmlFor="de-arrival" className="text-sm text-slate-300 cursor-pointer">
                  Include €1,200 initial arrival rental deposit (Kaution)
                </label>
              </div>
            </div>

            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-xs text-slate-300 space-y-2">
              <div className="flex items-center gap-1.5 text-orange-400 font-medium">
                <Info className="h-4 w-4" /> Statutory Auswärtiges Amt Rule
              </div>
              <p>
                German embassies require a minimum statutory blocked deposit of <strong>€992/month</strong>.
                Provider fees (Expatrio / Fintiba) and statutory buffer are required for account activation.
              </p>
            </div>
          </div>

          {/* Results Summary */}
          <div className="lg:col-span-7 space-y-6">
            <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 via-purple-500/5 to-transparent p-6 backdrop-blur-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-orange-400 mb-1">
                Required Blocked Account Deposit (Sperrkonto)
              </div>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-extrabold text-white">
                  €{deResult.total_blocked_deposit_required.toLocaleString()}
                </span>
                <span className="text-xl font-bold text-slate-300">
                  ≈ {deResult.total_first_year_liquidity_azn.toLocaleString()} AZN
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                {deResult.statutory_note}
              </p>
            </div>

            {/* Breakdown Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Monthly Payout</div>
                <div className="mt-1 text-lg font-bold text-white">€{deResult.statutory_monthly_amount}</div>
                <div className="text-[11px] text-slate-400">Statutory rate</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Health Insurance (TK/AOK)</div>
                <div className="mt-1 text-lg font-bold text-white">€{deResult.health_insurance_annual.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">€128.50/mo mandatory</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Semester Ticket & Fees</div>
                <div className="mt-1 text-lg font-bold text-white">€{deResult.semester_contributions_annual.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Transit pass included</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Provider & Buffer</div>
                <div className="mt-1 text-lg font-bold text-white">€189.00</div>
                <div className="text-[11px] text-slate-400">Expatrio / Fintiba fee</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Rental Deposit Kaution</div>
                <div className="mt-1 text-lg font-bold text-white">€{deResult.estimated_arrival_buffer.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Refundable deposit</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Total 1st Year Liquidity</div>
                <div className="mt-1 text-lg font-bold text-orange-400">€{deResult.total_first_year_liquidity_eur.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Total cash needed</div>
              </div>
            </div>

            {deResult.monthly_statutory_shortfall > 0 && (
              <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200">
                <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <strong>City Cost Alert:</strong> In {deResult.city_tier.replace(/_/g, " ")}, realistic monthly living expenses are approximately €{deResult.estimated_monthly_realistic_cost.toLocaleString()}, leaving a shortfall of €{deResult.monthly_statutory_shortfall}/month above the statutory blocked payout.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* 2. UK CAS MAINTENANCE TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "uk" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="h-5 w-5 text-orange-400" />
              UKVI Appendix Student Parameters
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Campus Location</label>
                <select
                  value={ukLocation}
                  onChange={(e) => setUkLocation(e.target.value as UKLocationType)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="outside_london" className="bg-slate-900 text-white">
                    Outside London (£1,023/month)
                  </option>
                  <option value="inner_london" className="bg-slate-900 text-white">
                    Inner London (£1,334/month)
                  </option>
                  <option value="outer_london" className="bg-slate-900 text-white">
                    Outer London (£1,334/month)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">CAS First-Year Tuition (£)</label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={ukTuition}
                  onChange={(e) => setUkTuition(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Tuition Deposit Paid on CAS (£)</label>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={ukDeposit}
                  onChange={(e) => setUkDeposit(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
                <span className="text-xs text-slate-400">Deducted from the 28-day holding requirement.</span>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <label className="text-slate-300 font-medium">Course Duration Assessed</label>
                  <span className="font-semibold text-white">{ukResult.maintenance_months_assessed} months (UKVI Cap: 9)</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="12"
                  value={ukDuration}
                  onChange={(e) => setUkDuration(Number(e.target.value))}
                  className="w-full accent-orange-500 cursor-pointer"
                />
              </div>
            </div>

            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-200 space-y-1.5">
              <div className="flex items-center gap-1.5 text-red-400 font-bold">
                <AlertTriangle className="h-4 w-4" /> Strict 28-Day Bank Statement Rule
              </div>
              <p>
                Funds must be held continuously for at least 28 consecutive days without dropping below the threshold for even one second prior to visa application date.
              </p>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 via-purple-500/5 to-transparent p-6 backdrop-blur-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-orange-400 mb-1">
                Strict 28-Day Bank Statement Requirement
              </div>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-extrabold text-white">
                  £{ukResult.total_funds_to_hold_28_days_gbp.toLocaleString()}
                </span>
                <span className="text-xl font-bold text-slate-300">
                  ≈ {ukResult.total_funds_in_azn.toLocaleString()} AZN
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                {ukResult.holding_rule_statement}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Monthly Rate</div>
                <div className="mt-1 text-lg font-bold text-white">£{ukResult.maintenance_monthly_rate_gbp}</div>
                <div className="text-[11px] text-slate-400">For 9 months max</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Maintenance Total</div>
                <div className="mt-1 text-lg font-bold text-white">£{ukResult.maintenance_total_gbp.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Living allowance</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Outstanding Tuition</div>
                <div className="mt-1 text-lg font-bold text-white">£{ukResult.outstanding_tuition_gbp.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Tuition minus deposit</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Health Surcharge (IHS)</div>
                <div className="mt-1 text-lg font-bold text-white">£{ukResult.immigration_health_surcharge_gbp}</div>
                <div className="text-[11px] text-slate-400">NHS access / year</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Visa Application Fee</div>
                <div className="mt-1 text-lg font-bold text-white">£{ukResult.visa_fee_gbp}</div>
                <div className="text-[11px] text-slate-400">Home Office fee</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Flight & Settling</div>
                <div className="mt-1 text-lg font-bold text-orange-400">£{ukResult.flight_and_settling_buffer_gbp}</div>
                <div className="text-[11px] text-slate-400">Initial travel buffer</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* 3. US FORM I-20 TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "usa" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="h-5 w-5 text-orange-400" />
              US Form I-20 & F-1 Parameters
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Annual Tuition ($)</label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={usTuition}
                  onChange={(e) => setUsTuition(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Mandatory Campus Fees ($)</label>
                <input
                  type="number"
                  min="0"
                  step="200"
                  value={usFees}
                  onChange={(e) => setUsFees(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Campus Living Location Tier</label>
                <select
                  value={usLocation}
                  onChange={(e) => setUsLocation(e.target.value as USLivingLocationTier)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="metropolitan_high" className="bg-slate-900 text-white">
                    Metropolitan High ($22,500/yr: NYC, Boston, SF, LA)
                  </option>
                  <option value="suburban_moderate" className="bg-slate-900 text-white">
                    Suburban Moderate ($16,500/yr: Austin, Chicago, Atlanta)
                  </option>
                  <option value="college_town_low" className="bg-slate-900 text-white">
                    College Town Low ($12,500/yr: Urbana, Ann Arbor, Lafayette)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Scholarship Award ($)</label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={usScholarship}
                  onChange={(e) => setUsScholarship(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="0"
                />
                <span className="text-xs text-slate-400">Deducted from gross Cost of Attendance.</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 via-purple-500/5 to-transparent p-6 backdrop-blur-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-orange-400 mb-1">
                Official Form I-20 Minimum Liquidity Required
              </div>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-extrabold text-white">
                  ${usResult.official_i20_total_usd.toLocaleString()}
                </span>
                <span className="text-xl font-bold text-slate-300">
                  ≈ {usResult.total_in_azn.toLocaleString()} AZN
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                {usResult.consular_advice}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Room & Board</div>
                <div className="mt-1 text-lg font-bold text-white">${usResult.living_room_and_board_usd.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Living allowance</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Health Insurance</div>
                <div className="mt-1 text-lg font-bold text-white">${usResult.health_insurance_usd.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Mandatory coverage</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">SEVIS I-901 Fee</div>
                <div className="mt-1 text-lg font-bold text-white">${usResult.sevis_fee_usd}</div>
                <div className="text-[11px] text-slate-400">DHS government fee</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">DS-160 MRV Fee</div>
                <div className="mt-1 text-lg font-bold text-white">${usResult.mrv_visa_fee_usd}</div>
                <div className="text-[11px] text-slate-400">Consular interview</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">15% Consular Cushion</div>
                <div className="mt-1 text-lg font-bold text-white">${usResult.recommended_consular_buffer_usd.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Discretion buffer</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Total Recommended</div>
                <div className="mt-1 text-lg font-bold text-orange-400">${usResult.total_recommended_affidavit_usd.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Safe affidavit sum</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* 4. ITALY ISEE-U TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "italy" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="h-5 w-5 text-orange-400" />
              Italy ISEE-U / DSU Grant Parameters
            </h2>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1.5">
                  <label className="text-slate-300 font-medium">Family Members in Household</label>
                  <span className="font-semibold text-white">{itMembers} persons</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={itMembers}
                  onChange={(e) => setItMembers(Number(e.target.value))}
                  className="w-full accent-orange-500 cursor-pointer"
                />
                <span className="text-xs text-slate-400">Equivalence scale increases with family size, lowering ISEE.</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Annual Family Income in Azerbaijan (AZN)</label>
                <input
                  type="number"
                  min="0"
                  step="2000"
                  value={itIncomeAzn}
                  onChange={(e) => setItIncomeAzn(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Residential Real Estate Valuation (AZN)</label>
                <input
                  type="number"
                  min="0"
                  step="10000"
                  value={itPropertyAzn}
                  onChange={(e) => setItPropertyAzn(Math.max(0, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
                <span className="text-xs text-slate-400">€52,500 statutory deduction applied to primary residence.</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">City Tier</label>
                <select
                  value={itCityTier}
                  onChange={(e) => setItCityTier(e.target.value as ItalyCityTier)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  <option value="tier_1_metropolitan" className="bg-slate-900 text-white">Tier 1: Milan, Rome (€950/mo)</option>
                  <option value="tier_2_major_student" className="bg-slate-900 text-white">Tier 2: Bologna, Turin, Florence (€780/mo)</option>
                  <option value="tier_3_regional" className="bg-slate-900 text-white">Tier 3: Padua, Pisa, Genoa (€620/mo)</option>
                  <option value="tier_4_southern" className="bg-slate-900 text-white">Tier 4: Naples, Bari, Palermo (€480/mo)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <div className={`rounded-2xl border p-6 backdrop-blur-xl ${
              itResult.qualifies_for_dsu_fee_waiver
                ? "border-emerald-500/30 bg-emerald-500/10"
                : "border-amber-500/30 bg-amber-500/10"
            }`}>
              <div className="flex items-center gap-2 mb-1">
                {itResult.qualifies_for_dsu_fee_waiver ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-amber-400" />
                )}
                <span className="text-xs font-semibold uppercase tracking-wider text-white">
                  ISEE Parificato Assessment: {itResult.qualifies_for_dsu_fee_waiver ? "DSU SCHOLARSHIP ELIGIBLE" : "SELF-FUNDED BRACKET"}
                </span>
              </div>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-extrabold text-white">
                  €{itResult.calculated_isee_parificato_eur.toLocaleString()}
                </span>
                <span className="text-sm font-medium text-slate-300">
                  (Ceiling: €25,000)
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-200 leading-relaxed">
                {itResult.dsu_eligibility_verdict}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Tuition After DSU</div>
                <div className="mt-1 text-lg font-bold text-white">€{itResult.annual_tuition_after_dsu_eur}</div>
                <div className="text-[11px] text-slate-400">
                  {itResult.qualifies_for_dsu_fee_waiver ? "Stamp duty only" : "Full tuition"}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Regional Cash Stipend</div>
                <div className="mt-1 text-lg font-bold text-emerald-400">€{itResult.estimated_dsu_cash_stipend_eur.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">Annual grant</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Annual Living Cost</div>
                <div className="mt-1 text-lg font-bold text-white">€{itResult.annual_living_cost_eur.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">€{itResult.monthly_living_cost_eur}/mo</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Permesso di Soggiorno</div>
                <div className="mt-1 text-lg font-bold text-white">€{itResult.permesso_di_soggiorno_fee_eur}</div>
                <div className="text-[11px] text-slate-400">Residence permit fee</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">SSN Health Insurance</div>
                <div className="mt-1 text-lg font-bold text-white">€{itResult.ssn_health_insurance_eur}</div>
                <div className="text-[11px] text-slate-400">Italian public healthcare</div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">Net First-Year Cost</div>
                <div className="mt-1 text-lg font-bold text-orange-400">€{itResult.net_first_year_cost_eur.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400">≈ {itResult.net_first_year_cost_azn.toLocaleString()} AZN</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* 5. COMPARE 4 COUNTRIES TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "compare" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <label className="text-sm font-semibold text-white">Your Disposable First-Year Budget (AZN)</label>
                <p className="text-xs text-slate-400">Benchmark your liquid savings against statutory visa thresholds.</p>
              </div>
              <div className="text-2xl font-extrabold text-orange-400">
                {compareBudgetAzn.toLocaleString()} AZN
              </div>
            </div>
            <input
              type="range"
              min="5000"
              max="90000"
              step="2500"
              value={compareBudgetAzn}
              onChange={(e) => setCompareBudgetAzn(Number(e.target.value))}
              className="w-full accent-orange-500 cursor-pointer"
            />
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 text-sm text-slate-300">
              <span className="font-semibold text-white">Verdict: </span>
              {compareResult.summary_verdict}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {compareResult.destinations.map((dest) => (
              <div
                key={dest.country}
                className={`rounded-2xl border p-5 backdrop-blur-xl flex flex-col justify-between transition-all hover:scale-[1.02] ${
                  dest.is_within_budget
                    ? "border-emerald-500/40 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                    : "border-red-500/30 bg-red-500/5"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-white">{dest.country}</span>
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        dest.is_within_budget
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-red-500/20 text-red-300 border border-red-500/30"
                      }`}
                    >
                      {dest.is_within_budget ? "Within Budget" : "Shortfall"}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400 font-medium">
                    {dest.visa_category}
                  </div>

                  <div className="pt-2 border-t border-white/[0.06]">
                    <div className="text-xs text-slate-400">Total 1st Year Cost (AZN)</div>
                    <div className="text-2xl font-extrabold text-white">
                      {dest.total_first_year_cost_azn.toLocaleString()} AZN
                    </div>
                    <div className="text-xs text-slate-400">
                      ≈ {dest.total_first_year_cost_native.toLocaleString()} {dest.currency}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs">
                    {dest.budget_delta_azn >= 0 ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <TrendingUp className="h-3.5 w-3.5" /> +{dest.budget_delta_azn.toLocaleString()} AZN buffer
                      </span>
                    ) : (
                      <span className="text-red-400 flex items-center gap-1">
                        <TrendingDown className="h-3.5 w-3.5" /> {dest.budget_delta_azn.toLocaleString()} AZN gap
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-white/[0.06] text-[11px] text-slate-400 leading-normal">
                  {dest.key_regulatory_condition}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* 6. MULTI-CURRENCY CONVERTER TAB */}
      {/* --------------------------------------------------------- */}
      {activeTab === "converter" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <ArrowRightLeft className="h-5 w-5 text-orange-400" />
              Real-Time CBAR Currency Converter
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Amount</label>
                <input
                  type="number"
                  min="1"
                  step="100"
                  value={convAmount}
                  onChange={(e) => setConvAmount(Math.max(1, Number(e.target.value)))}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">From</label>
                  <select
                    value={fromCurr}
                    onChange={(e) => setFromCurr(e.target.value as Currency)}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    {(Object.keys(FALLBACK_RATES_TO_AZN) as Currency[]).map((c) => (
                      <option key={c} value={c} className="bg-slate-900 text-white">
                        {c}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">To</label>
                  <select
                    value={toCurr}
                    onChange={(e) => setToCurr(e.target.value as Currency)}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.06] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    {(Object.keys(FALLBACK_RATES_TO_AZN) as Currency[]).map((c) => (
                      <option key={c} value={c} className="bg-slate-900 text-white">
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-xs text-slate-300 space-y-1.5">
              <div className="font-semibold text-white">Official CBAR Fixed Rate Matrix</div>
              <p>1 USD = 1.7000 AZN | 1 EUR = 1.8540 AZN | 1 GBP = 2.2180 AZN | 1 TRY = 0.0495 AZN</p>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 via-purple-500/5 to-transparent p-6 backdrop-blur-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-orange-400 mb-1">
                Converted Output
              </div>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-4xl sm:text-5xl font-extrabold text-white">
                  {convertedResult.converted.toLocaleString()} {toCurr}
                </span>
                <span className="text-sm text-slate-400">
                  (1 {fromCurr} = {convertedResult.rate} {toCurr})
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">In AZN (Manat)</div>
                <div className="mt-1 text-lg font-bold text-white">
                  {convertedResult.breakdown.AZN.toLocaleString()} ₼
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">In EUR (Euro)</div>
                <div className="mt-1 text-lg font-bold text-white">
                  €{convertedResult.breakdown.EUR.toLocaleString()}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">In USD (Dollar)</div>
                <div className="mt-1 text-lg font-bold text-white">
                  ${convertedResult.breakdown.USD.toLocaleString()}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-xs text-slate-400">In GBP (Pound)</div>
                <div className="mt-1 text-lg font-bold text-white">
                  £{convertedResult.breakdown.GBP.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

