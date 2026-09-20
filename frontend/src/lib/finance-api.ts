/**
 * Client API library and domain models for Student Visa, Blocked Account & Living Cost Simulator.
 */

import { API_BASE_URL } from "@/lib/api";

export type Currency = "AZN" | "EUR" | "USD" | "GBP" | "TRY" | "PLN" | "HUF";

export type GermanCityTier = "tier_1_expensive" | "tier_2_moderate" | "tier_3_affordable";

export type UKLocationType = "inner_london" | "outer_london" | "outside_london";

export type USLivingLocationTier = "metropolitan_high" | "suburban_moderate" | "college_town_low";

export type ItalyCityTier = "tier_1_metropolitan" | "tier_2_major_student" | "tier_3_regional" | "tier_4_southern";

export interface ExchangeRatesResponse {
  base_currency: string;
  rates_to_azn: Record<string, number>;
  cross_rates: Record<string, Record<string, number>>;
}

export interface CurrencyConversionRequest {
  amount: number;
  from_currency: Currency;
  to_currency: Currency;
  safety_buffer_pct?: number;
}

export interface CurrencyConversionResponse {
  amount: number;
  from_currency: Currency;
  to_currency: Currency;
  exchange_rate: number;
  converted_amount: number;
  converted_all_major: Record<string, number>;
}

export interface GermanyCalcRequest {
  months?: number;
  city_tier?: GermanCityTier;
  tuition_fee_eur?: number;
  include_arrival_buffer?: boolean;
  exchange_safety_buffer_pct?: number;
}

export interface GermanyProofOfFundsResponse {
  country: string;
  statutory_monthly_amount: number;
  number_of_months: number;
  blocked_account_total: number;
  account_setup_fee: number;
  account_buffer_deposit: number;
  total_blocked_deposit_required: number;
  health_insurance_annual: number;
  semester_contributions_annual: number;
  visa_fee: number;
  estimated_arrival_buffer: number;
  total_first_year_liquidity_eur: number;
  total_first_year_liquidity_azn: number;
  total_in_all_currencies: Record<string, number>;
  city_tier: string;
  estimated_monthly_realistic_cost: number;
  monthly_statutory_shortfall: number;
  statutory_note: string;
  breakdown: Record<string, number>;
}

export interface UKCalcRequest {
  location_type?: UKLocationType;
  course_tuition_annual_gbp?: number;
  deposit_paid_to_cas_gbp?: number;
  course_duration_months?: number;
  exchange_safety_buffer_pct?: number;
}

export interface UKProofOfFundsResponse {
  country: string;
  location_type: string;
  maintenance_monthly_rate_gbp: number;
  maintenance_months_assessed: number;
  maintenance_total_gbp: number;
  course_tuition_annual_gbp: number;
  deposit_paid_to_cas_gbp: number;
  outstanding_tuition_gbp: number;
  immigration_health_surcharge_gbp: number;
  visa_fee_gbp: number;
  flight_and_settling_buffer_gbp: number;
  total_funds_to_hold_28_days_gbp: number;
  total_funds_in_azn: number;
  total_in_all_currencies: Record<string, number>;
  holding_rule_statement: string;
  breakdown: Record<string, number>;
}

export interface USCalcRequest {
  tuition_annual_usd?: number;
  institutional_fees_usd?: number;
  location_tier?: USLivingLocationTier;
  scholarship_award_usd?: number;
  exchange_safety_buffer_pct?: number;
}

export interface USProofOfFundsResponse {
  country: string;
  tuition_annual_usd: number;
  mandatory_institutional_fees_usd: number;
  living_room_and_board_usd: number;
  health_insurance_usd: number;
  books_and_supplies_usd: number;
  personal_and_transport_usd: number;
  official_i20_total_usd: number;
  sevis_fee_usd: number;
  mrv_visa_fee_usd: number;
  recommended_consular_buffer_usd: number;
  total_recommended_affidavit_usd: number;
  total_in_azn: number;
  total_in_all_currencies: Record<string, number>;
  consular_advice: string;
  breakdown: Record<string, number>;
}

export interface ItalyCalcRequest {
  family_members_count?: number;
  family_annual_income_azn?: number;
  real_estate_abroad_azn?: number;
  city_tier?: ItalyCityTier;
  base_tuition_eur?: number;
  exchange_safety_buffer_pct?: number;
}

export interface ItalyProofOfFundsResponse {
  country: string;
  calculated_isee_parificato_eur: number;
  qualifies_for_dsu_fee_waiver: boolean;
  qualifies_for_dsu_cash_stipend: boolean;
  estimated_dsu_cash_stipend_eur: number;
  annual_tuition_after_dsu_eur: number;
  monthly_living_cost_eur: number;
  annual_living_cost_eur: number;
  permesso_di_soggiorno_fee_eur: number;
  ssn_health_insurance_eur: number;
  net_first_year_cost_eur: number;
  net_first_year_cost_azn: number;
  total_in_all_currencies: Record<string, number>;
  dsu_eligibility_verdict: string;
  breakdown: Record<string, number>;
}

export interface DestinationCompareRequest {
  student_annual_budget_azn?: number;
  tuition_eur?: number;
  tuition_gbp?: number;
  tuition_usd?: number;
  tuition_italy_eur?: number;
  family_members_count?: number;
  family_income_azn?: number;
}

export interface DestinationComparisonItem {
  country: string;
  currency: string;
  visa_category: string;
  statutory_deposit_native: number;
  total_first_year_cost_native: number;
  total_first_year_cost_azn: number;
  is_within_budget: boolean;
  budget_delta_azn: number;
  key_regulatory_condition: string;
}

export interface DestinationCompareResponse {
  student_budget_azn: number;
  destinations: DestinationComparisonItem[];
  most_affordable_country: string;
  highest_liquidity_country: string;
  summary_verdict: string;
}

// ==============================================================================
// BASELINE CBAR FALLBACK RATES
// ==============================================================================
export const FALLBACK_RATES_TO_AZN: Record<Currency, number> = {
  AZN: 1.0,
  USD: 1.70,
  EUR: 1.854,
  GBP: 2.218,
  TRY: 0.0495,
  PLN: 0.432,
  HUF: 0.0047,
};

// ==============================================================================
// LOCAL FALLBACK CALCULATORS (instant zero-latency client computation)
// ==============================================================================

export function calculateGermanyLocal(req: GermanyCalcRequest = {}): GermanyProofOfFundsResponse {
  const months = Math.max(1, req.months ?? 12);
  const cityTier = req.city_tier ?? "tier_2_moderate";
  const tuition = Math.max(0, req.tuition_fee_eur ?? 0);
  const arrival = req.include_arrival_buffer !== false ? 1200 : 0;
  const fxBuffer = (req.exchange_safety_buffer_pct ?? 3.0) / 100;

  const monthlyStatutory = 992.0;
  const blockedBase = monthlyStatutory * months;
  const setupFee = 89.0;
  const providerBuffer = 100.0;
  const totalBlocked = blockedBase + setupFee + providerBuffer;

  const healthAnnual = 128.5 * months;
  const semesters = Math.ceil(months / 6);
  const semesterContributions = 310 * semesters;
  const visaFee = 75.0;

  const multipliers: Record<GermanCityTier, number> = {
    tier_1_expensive: 1.18,
    tier_2_moderate: 1.0,
    tier_3_affordable: 0.88,
  };
  const realisticMonthly = Math.round(monthlyStatutory * (multipliers[cityTier] || 1.0) * 100) / 100;
  const shortfall = Math.max(0, realisticMonthly - monthlyStatutory);

  const totalEur = totalBlocked + healthAnnual + semesterContributions + visaFee + tuition + arrival;
  const totalAzn = Math.round(totalEur * FALLBACK_RATES_TO_AZN.EUR * (1 + fxBuffer) * 100) / 100;

  return {
    country: "Germany",
    statutory_monthly_amount: monthlyStatutory,
    number_of_months: months,
    blocked_account_total: blockedBase,
    account_setup_fee: setupFee,
    account_buffer_deposit: providerBuffer,
    total_blocked_deposit_required: totalBlocked,
    health_insurance_annual: healthAnnual,
    semester_contributions_annual: semesterContributions,
    visa_fee: visaFee,
    estimated_arrival_buffer: arrival,
    total_first_year_liquidity_eur: totalEur,
    total_first_year_liquidity_azn: totalAzn,
    total_in_all_currencies: {
      AZN: totalAzn,
      EUR: totalEur,
      USD: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.USD) * 100) / 100,
      GBP: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.GBP) * 100) / 100,
    },
    city_tier: cityTier,
    estimated_monthly_realistic_cost: realisticMonthly,
    monthly_statutory_shortfall: shortfall,
    statutory_note: `Statutory Sperrkonto base is €${monthlyStatutory} per month (€${blockedBase.toLocaleString()} for ${months} months). Provider setup fee (€89) and emergency buffer (€100) are included in the bank transfer total.`,
    breakdown: {
      blocked_account_base_eur: blockedBase,
      provider_setup_and_buffer_eur: setupFee + providerBuffer,
      health_insurance_eur: healthAnnual,
      semester_contributions_eur: semesterContributions,
      tuition_fees_eur: tuition,
      arrival_rental_deposit_eur: arrival,
      visa_fee_eur: visaFee,
    },
  };
}

export function calculateUKLocal(req: UKCalcRequest = {}): UKProofOfFundsResponse {
  const location = req.location_type ?? "outside_london";
  const tuition = Math.max(0, req.course_tuition_annual_gbp ?? 18500);
  const deposit = Math.min(tuition, Math.max(0, req.deposit_paid_to_cas_gbp ?? 2000));
  const monthsAssessed = Math.min(9, Math.max(1, req.course_duration_months ?? 9));
  const fxBuffer = (req.exchange_safety_buffer_pct ?? 3.0) / 100;

  const monthlyRate = location === "outside_london" ? 1023.0 : 1334.0;
  const maintenanceTotal = monthlyRate * monthsAssessed;
  const outstandingTuition = tuition - deposit;
  const ihsFee = 776.0;
  const visaFee = 490.0;
  const buffer = 800.0;

  const strict28Day = maintenanceTotal + outstandingTuition;
  const totalGbp = strict28Day + ihsFee + visaFee + buffer;
  const totalAzn = Math.round(totalGbp * FALLBACK_RATES_TO_AZN.GBP * (1 + fxBuffer) * 100) / 100;

  return {
    country: "United Kingdom",
    location_type: location,
    maintenance_monthly_rate_gbp: monthlyRate,
    maintenance_months_assessed: monthsAssessed,
    maintenance_total_gbp: maintenanceTotal,
    course_tuition_annual_gbp: tuition,
    deposit_paid_to_cas_gbp: deposit,
    outstanding_tuition_gbp: outstandingTuition,
    immigration_health_surcharge_gbp: ihsFee,
    visa_fee_gbp: visaFee,
    flight_and_settling_buffer_gbp: buffer,
    total_funds_to_hold_28_days_gbp: totalGbp,
    total_funds_in_azn: totalAzn,
    total_in_all_currencies: {
      AZN: totalAzn,
      GBP: totalGbp,
      EUR: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.EUR) * 100) / 100,
      USD: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.USD) * 100) / 100,
    },
    holding_rule_statement: `UKVI strictly requires £${strict28Day.toLocaleString()} (£${maintenanceTotal.toLocaleString()} maintenance + £${outstandingTuition.toLocaleString()} outstanding tuition) to be held continuously in bank account for at least 28 consecutive days.`,
    breakdown: {
      monthly_maintenance_rate_gbp: monthlyRate,
      maintenance_total_gbp: maintenanceTotal,
      outstanding_tuition_gbp: outstandingTuition,
      immigration_health_surcharge_gbp: ihsFee,
      visa_application_fee_gbp: visaFee,
      strict_28_day_bank_statement_requirement_gbp: strict28Day,
    },
  };
}

export function calculateUSLocal(req: USCalcRequest = {}): USProofOfFundsResponse {
  const tuition = Math.max(0, req.tuition_annual_usd ?? 28000);
  const fees = Math.max(0, req.institutional_fees_usd ?? 1800);
  const location = req.location_tier ?? "suburban_moderate";
  const scholarship = Math.max(0, req.scholarship_award_usd ?? 0);
  const fxBuffer = (req.exchange_safety_buffer_pct ?? 3.0) / 100;

  const roomBoardMap: Record<USLivingLocationTier, number> = {
    metropolitan_high: 22500,
    suburban_moderate: 16500,
    college_town_low: 12500,
  };
  const roomBoard = roomBoardMap[location] || 16500;
  const health = 2400.0;
  const books = 1200.0;
  const personal = 2200.0;

  const grossI20 = tuition + fees + roomBoard + health + books + personal;
  const netI20 = Math.max(0, grossI20 - scholarship);
  const sevis = 350.0;
  const visaFee = 185.0;
  const buffer = Math.round(netI20 * 0.15 * 100) / 100;

  const totalUsd = netI20 + sevis + visaFee + buffer;
  const totalAzn = Math.round(totalUsd * FALLBACK_RATES_TO_AZN.USD * (1 + fxBuffer) * 100) / 100;

  return {
    country: "United States",
    tuition_annual_usd: tuition,
    mandatory_institutional_fees_usd: fees,
    living_room_and_board_usd: roomBoard,
    health_insurance_usd: health,
    books_and_supplies_usd: books,
    personal_and_transport_usd: personal,
    official_i20_total_usd: netI20,
    sevis_fee_usd: sevis,
    mrv_visa_fee_usd: visaFee,
    recommended_consular_buffer_usd: buffer,
    total_recommended_affidavit_usd: totalUsd,
    total_in_azn: totalAzn,
    total_in_all_currencies: {
      AZN: totalAzn,
      USD: totalUsd,
      EUR: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.EUR) * 100) / 100,
      GBP: Math.round((totalAzn / FALLBACK_RATES_TO_AZN.GBP) * 100) / 100,
    },
    consular_advice: `Your official Form I-20 will mandate $${netI20.toLocaleString()} minimum funding. We recommend demonstrating $${totalUsd.toLocaleString()} with liquid assets at the Baku consular interview.`,
    breakdown: {
      tuition_usd: tuition,
      mandatory_fees_usd: fees,
      room_and_board_usd: roomBoard,
      health_insurance_usd: health,
      books_and_supplies_usd: books,
      personal_expenses_usd: personal,
      scholarship_deduction_usd: scholarship,
      official_net_i20_usd: netI20,
      sevis_fee_usd: sevis,
      mrv_visa_fee_usd: visaFee,
      consular_safety_buffer_usd: buffer,
    },
  };
}

export function calculateItalyLocal(req: ItalyCalcRequest = {}): ItalyProofOfFundsResponse {
  const members = Math.max(1, req.family_members_count ?? 4);
  const incomeAzn = Math.max(0, req.family_annual_income_azn ?? 24000);
  const propertyAzn = Math.max(0, req.real_estate_abroad_azn ?? 80000);
  const cityTier = req.city_tier ?? "tier_2_major_student";
  const baseTuition = Math.max(0, req.base_tuition_eur ?? 3500);
  const fxBuffer = (req.exchange_safety_buffer_pct ?? 3.0) / 100;

  const scales: Record<number, number> = { 1: 1.0, 2: 1.57, 3: 2.04, 4: 2.46, 5: 2.85 };
  const scale = scales[members] || (2.85 + (members - 5) * 0.35);

  const incomeEur = incomeAzn / FALLBACK_RATES_TO_AZN.EUR;
  const propertyEur = propertyAzn / FALLBACK_RATES_TO_AZN.EUR;
  const netProperty = Math.max(0, propertyEur - 52500);
  const patrimony = netProperty * 0.2;

  const isee = Math.round(((incomeEur + patrimony) / scale) * 100) / 100;
  const qualifies = isee <= 25000;
  const qualifiesTop = isee <= 15000;

  const tuitionAfterDsu = qualifies ? 156.0 : baseTuition;
  const stipend = qualifies ? (qualifiesTop ? 7200.0 : 4500.0) : 0.0;

  const livingRates: Record<ItalyCityTier, number> = {
    tier_1_metropolitan: 950,
    tier_2_major_student: 780,
    tier_3_regional: 620,
    tier_4_southern: 480,
  };
  const monthlyLiving = livingRates[cityTier] || 780;
  const annualLiving = monthlyLiving * 12;
  const permesso = 118.0;
  const ssn = 700.0;

  const grossCost = tuitionAfterDsu + annualLiving + permesso + ssn;
  const netCost = Math.max(0, grossCost - stipend);
  const netAzn = Math.round(netCost * FALLBACK_RATES_TO_AZN.EUR * (1 + fxBuffer) * 100) / 100;

  return {
    country: "Italy",
    calculated_isee_parificato_eur: isee,
    qualifies_for_dsu_fee_waiver: qualifies,
    qualifies_for_dsu_cash_stipend: qualifies,
    estimated_dsu_cash_stipend_eur: stipend,
    annual_tuition_after_dsu_eur: tuitionAfterDsu,
    monthly_living_cost_eur: monthlyLiving,
    annual_living_cost_eur: annualLiving,
    permesso_di_soggiorno_fee_eur: permesso,
    ssn_health_insurance_eur: ssn,
    net_first_year_cost_eur: netCost,
    net_first_year_cost_azn: netAzn,
    total_in_all_currencies: {
      AZN: netAzn,
      EUR: netCost,
      USD: Math.round((netAzn / FALLBACK_RATES_TO_AZN.USD) * 100) / 100,
      GBP: Math.round((netAzn / FALLBACK_RATES_TO_AZN.GBP) * 100) / 100,
    },
    dsu_eligibility_verdict: qualifies
      ? `Your ISEE Parificato of €${isee.toLocaleString()} is below the €25,000 threshold. You qualify for 100% tuition exemption plus €${stipend.toLocaleString()}/yr regional stipend.`
      : `Your ISEE Parificato of €${isee.toLocaleString()} exceeds the €25,000 threshold. Standard intermediate tuition applies.`,
    breakdown: {
      family_income_eur: Math.round(incomeEur),
      property_valuation_eur: Math.round(propertyEur),
      equivalence_scale_factor: scale,
      calculated_isee_parificato_eur: isee,
      tuition_payable_eur: tuitionAfterDsu,
      annual_living_cost_eur: annualLiving,
      dsu_scholarship_stipend_eur: stipend,
      permesso_fee_eur: permesso,
      ssn_health_insurance_eur: ssn,
    },
  };
}

export function compareDestinationsLocal(req: DestinationCompareRequest = {}): DestinationCompareResponse {
  const budget = Math.max(0, req.student_annual_budget_azn ?? 35000);
  const de = calculateGermanyLocal({ tuition_fee_eur: req.tuition_eur });
  const uk = calculateUKLocal({ course_tuition_annual_gbp: req.tuition_gbp });
  const us = calculateUSLocal({ tuition_annual_usd: req.tuition_usd });
  const it = calculateItalyLocal({
    family_members_count: req.family_members_count,
    family_annual_income_azn: req.family_income_azn,
    base_tuition_eur: req.tuition_italy_eur,
  });

  const destinations: DestinationComparisonItem[] = [
    {
      country: "Germany",
      currency: "EUR",
      visa_category: "Sperrkonto (Blocked Account § 16b)",
      statutory_deposit_native: de.total_blocked_deposit_required,
      total_first_year_cost_native: de.total_first_year_liquidity_eur,
      total_first_year_cost_azn: de.total_first_year_liquidity_azn,
      is_within_budget: budget >= de.total_first_year_liquidity_azn,
      budget_delta_azn: Math.round((budget - de.total_first_year_liquidity_azn) * 100) / 100,
      key_regulatory_condition: "€11,904 blocked in verified account before visa interview.",
    },
    {
      country: "United Kingdom",
      currency: "GBP",
      visa_category: "CAS Maintenance (Appendix Student)",
      statutory_deposit_native: uk.total_funds_to_hold_28_days_gbp,
      total_first_year_cost_native: uk.total_funds_to_hold_28_days_gbp,
      total_first_year_cost_azn: uk.total_funds_in_azn,
      is_within_budget: budget >= uk.total_funds_in_azn,
      budget_delta_azn: Math.round((budget - uk.total_funds_in_azn) * 100) / 100,
      key_regulatory_condition: "Funds must be held continuously in bank account for 28 consecutive days.",
    },
    {
      country: "United States",
      currency: "USD",
      visa_category: "Form I-20 Full Cost Affidavit (F-1)",
      statutory_deposit_native: us.official_i20_total_usd,
      total_first_year_cost_native: us.total_recommended_affidavit_usd,
      total_first_year_cost_azn: us.total_in_azn,
      is_within_budget: budget >= us.total_in_azn,
      budget_delta_azn: Math.round((budget - us.total_in_azn) * 100) / 100,
      key_regulatory_condition: "Proof of liquid funding covering full official I-20 Cost of Attendance.",
    },
    {
      country: "Italy",
      currency: "EUR",
      visa_category: "ISEE-U / Regional DSU Grant",
      statutory_deposit_native: it.net_first_year_cost_eur,
      total_first_year_cost_native: it.net_first_year_cost_eur,
      total_first_year_cost_azn: it.net_first_year_cost_azn,
      is_within_budget: budget >= it.net_first_year_cost_azn,
      budget_delta_azn: Math.round((budget - it.net_first_year_cost_azn) * 100) / 100,
      key_regulatory_condition: "ISEE Parificato certification unlocks 100% tuition waiver and regional cash stipend.",
    },
  ];

  destinations.sort((a, b) => a.total_first_year_cost_azn - b.total_first_year_cost_azn);
  const mostAffordable = destinations[0].country;
  const highest = destinations[destinations.length - 1].country;

  return {
    student_budget_azn: budget,
    destinations,
    most_affordable_country: mostAffordable,
    highest_liquidity_country: highest,
    summary_verdict: `With an annual budget of ${budget.toLocaleString()} AZN, ${mostAffordable} provides the most accessible financial route. ${highest} requires the highest initial cash demonstration.`,
  };
}

// ==============================================================================
// ASYNC API CLIENT WRAPPERS (With Graceful Fallbacks)
// ==============================================================================

export async function fetchExchangeRates(): Promise<ExchangeRatesResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/rates`, { method: "GET" });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Graceful fallback to static CBAR peg rates
  }
  return {
    base_currency: "AZN",
    rates_to_azn: FALLBACK_RATES_TO_AZN,
    cross_rates: {},
  };
}

export async function fetchGermanyCalculation(req: GermanyCalcRequest): Promise<GermanyProofOfFundsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/germany`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to local math
  }
  return calculateGermanyLocal(req);
}

export async function fetchUKCalculation(req: UKCalcRequest): Promise<UKProofOfFundsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/uk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to local math
  }
  return calculateUKLocal(req);
}

export async function fetchUSCalculation(req: USCalcRequest): Promise<USProofOfFundsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/usa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to local math
  }
  return calculateUSLocal(req);
}

export async function fetchItalyCalculation(req: ItalyCalcRequest): Promise<ItalyProofOfFundsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/italy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to local math
  }
  return calculateItalyLocal(req);
}

export async function fetchDestinationComparison(req: DestinationCompareRequest): Promise<DestinationCompareResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/finance/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to local math
  }
  return compareDestinationsLocal(req);
}
