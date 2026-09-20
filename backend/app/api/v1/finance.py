"""API Router for Student Visa, Blocked Account & Living Cost Simulator.

Implements statutory proof-of-funds endpoints for Germany, UK, US, Italy,
real-time multi-currency conversions, and cross-destination budget comparison.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.domain.financial_calculator import (
    Currency,
    GermanCityTier,
    UKLocationType,
    USLivingLocationTier,
    ItalyCityTier,
    EXCHANGE_RATES_TO_AZN,
    get_exchange_rate,
    convert_amount,
    convert_to_all_major,
    calculate_germany_funds,
    calculate_uk_funds,
    calculate_us_funds,
    calculate_italy_funds,
    compare_study_destinations_finance,
)

router = APIRouter(prefix="/finance", tags=["Financial & Visa Simulator"])


# ==============================================================================
# SCHEMAS
# ==============================================================================

class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to convert")
    from_currency: Currency = Field(..., description="Source currency ISO code")
    to_currency: Currency = Field(..., description="Target currency ISO code")
    safety_buffer_pct: float = Field(0.0, ge=0.0, le=25.0, description="FX fluctuation safety cushion percentage (0-25%)")


class CurrencyConversionResponse(BaseModel):
    amount: float
    from_currency: Currency
    to_currency: Currency
    exchange_rate: float
    converted_amount: float
    converted_all_major: Dict[str, float]


class ExchangeRatesResponse(BaseModel):
    base_currency: str = "AZN"
    rates_to_azn: Dict[str, float]
    cross_rates: Dict[str, Dict[str, float]]


class GermanyCalcRequest(BaseModel):
    months: int = Field(12, ge=1, le=48, description="Study duration in months (standard 12 for 1 academic year)")
    city_tier: GermanCityTier = Field(GermanCityTier.TIER_2_MODERATE, description="City expense tier")
    tuition_fee_eur: float = Field(0.0, ge=0.0, description="Annual tuition fee (0 for public German universities)")
    include_arrival_buffer: bool = Field(True, description="Include €1,200 rental deposit / initial setup buffer")
    exchange_safety_buffer_pct: float = Field(3.0, ge=0.0, le=20.0, description="FX safety buffer percentage")


class GermanyProofOfFundsResponse(BaseModel):
    country: str = "Germany"
    statutory_monthly_amount: float
    number_of_months: int
    blocked_account_total: float
    account_setup_fee: float
    account_buffer_deposit: float
    total_blocked_deposit_required: float
    health_insurance_annual: float
    semester_contributions_annual: float
    visa_fee: float
    estimated_arrival_buffer: float
    total_first_year_liquidity_eur: float
    total_first_year_liquidity_azn: float
    total_in_all_currencies: Dict[str, float]
    city_tier: str
    estimated_monthly_realistic_cost: float
    monthly_statutory_shortfall: float
    statutory_note: str
    breakdown: Dict[str, float]


class UKCalcRequest(BaseModel):
    location_type: UKLocationType = Field(UKLocationType.OUTSIDE_LONDON, description="Inner/Outer London vs Outside London")
    course_tuition_annual_gbp: float = Field(18500.0, ge=0.0, description="First-year tuition fee as stated on CAS")
    deposit_paid_to_cas_gbp: float = Field(2000.0, ge=0.0, description="Advance tuition deposit logged on CAS statement")
    course_duration_months: int = Field(9, ge=1, le=48, description="Course length (UKVI caps maintenance assessment at 9 months)")
    exchange_safety_buffer_pct: float = Field(3.0, ge=0.0, le=20.0, description="FX safety buffer percentage")


class UKProofOfFundsResponse(BaseModel):
    country: str = "United Kingdom"
    location_type: str
    maintenance_monthly_rate_gbp: float
    maintenance_months_assessed: int
    maintenance_total_gbp: float
    course_tuition_annual_gbp: float
    deposit_paid_to_cas_gbp: float
    outstanding_tuition_gbp: float
    immigration_health_surcharge_gbp: float
    visa_fee_gbp: float
    flight_and_settling_buffer_gbp: float
    total_funds_to_hold_28_days_gbp: float
    total_funds_in_azn: float
    total_in_all_currencies: Dict[str, float]
    holding_rule_statement: str
    breakdown: Dict[str, float]


class USCalcRequest(BaseModel):
    tuition_annual_usd: float = Field(28000.0, ge=0.0, description="Annual tuition cost stated by university")
    institutional_fees_usd: float = Field(1800.0, ge=0.0, description="Mandatory university fees")
    location_tier: USLivingLocationTier = Field(USLivingLocationTier.SUBURBAN_MODERATE, description="Campus living tier")
    scholarship_award_usd: float = Field(0.0, ge=0.0, description="Institutional scholarship award deducting from I-20")
    exchange_safety_buffer_pct: float = Field(3.0, ge=0.0, le=20.0, description="FX safety buffer percentage")


class USProofOfFundsResponse(BaseModel):
    country: str = "United States"
    tuition_annual_usd: float
    mandatory_institutional_fees_usd: float
    living_room_and_board_usd: float
    health_insurance_usd: float
    books_and_supplies_usd: float
    personal_and_transport_usd: float
    official_i20_total_usd: float
    sevis_fee_usd: float
    mrv_visa_fee_usd: float
    recommended_consular_buffer_usd: float
    total_recommended_affidavit_usd: float
    total_in_azn: float
    total_in_all_currencies: Dict[str, float]
    consular_advice: str
    breakdown: Dict[str, float]


class ItalyCalcRequest(BaseModel):
    family_members_count: int = Field(4, ge=1, le=12, description="Total nuclear family members residing in household")
    family_annual_income_azn: float = Field(24000.0, ge=0.0, description="Gross total household annual earnings in Azerbaijan")
    real_estate_abroad_azn: float = Field(80000.0, ge=0.0, description="Total residential real estate value owned in Azerbaijan")
    city_tier: ItalyCityTier = Field(ItalyCityTier.TIER_2_MAJOR_STUDENT, description="Italian university city location tier")
    base_tuition_eur: float = Field(3500.0, ge=0.0, description="Standard maximum university tuition prior to DSU waiver")
    exchange_safety_buffer_pct: float = Field(3.0, ge=0.0, le=20.0, description="FX safety buffer percentage")


class ItalyProofOfFundsResponse(BaseModel):
    country: str = "Italy"
    calculated_isee_parificato_eur: float
    qualifies_for_dsu_fee_waiver: bool
    qualifies_for_dsu_cash_stipend: bool
    estimated_dsu_cash_stipend_eur: float
    annual_tuition_after_dsu_eur: float
    monthly_living_cost_eur: float
    annual_living_cost_eur: float
    permesso_di_soggiorno_fee_eur: float
    ssn_health_insurance_eur: float
    net_first_year_cost_eur: float
    net_first_year_cost_azn: float
    total_in_all_currencies: Dict[str, float]
    dsu_eligibility_verdict: str
    breakdown: Dict[str, float]


class DestinationCompareRequest(BaseModel):
    student_annual_budget_azn: float = Field(35000.0, ge=0.0, description="Total disposable 1st-year budget in AZN")
    tuition_eur: float = Field(0.0, ge=0.0, description="Germany tuition fee")
    tuition_gbp: float = Field(18000.0, ge=0.0, description="UK tuition fee")
    tuition_usd: float = Field(28000.0, ge=0.0, description="US tuition fee")
    tuition_italy_eur: float = Field(3500.0, ge=0.0, description="Italy base tuition fee")
    family_members_count: int = Field(4, ge=1, le=12, description="Family members for Italy ISEE-U calculation")
    family_income_azn: float = Field(24000.0, ge=0.0, description="Family income in AZN for Italy ISEE-U")


class DestinationComparisonItem(BaseModel):
    country: str
    currency: str
    visa_category: str
    statutory_deposit_native: float
    total_first_year_cost_native: float
    total_first_year_cost_azn: float
    is_within_budget: bool
    budget_delta_azn: float
    key_regulatory_condition: str


class DestinationCompareResponse(BaseModel):
    student_budget_azn: float
    destinations: List[DestinationComparisonItem]
    most_affordable_country: str
    highest_liquidity_country: str
    summary_verdict: str


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/rates", response_model=ExchangeRatesResponse)
async def get_exchange_rates():
    """Returns official Central Bank of Azerbaijan (CBAR) reference rates and multi-currency matrix."""
    rates_azn = {curr.value: float(rate) for curr, rate in EXCHANGE_RATES_TO_AZN.items()}
    
    major_currencies = [Currency.AZN, Currency.EUR, Currency.USD, Currency.GBP, Currency.TRY, Currency.PLN, Currency.HUF]
    cross_matrix: Dict[str, Dict[str, float]] = {}
    for from_c in major_currencies:
        cross_matrix[from_c.value] = {}
        for to_c in major_currencies:
            rate = float(get_exchange_rate(from_c, to_c))
            cross_matrix[from_c.value][to_c.value] = round(rate, 4)

    return ExchangeRatesResponse(
        base_currency="AZN",
        rates_to_azn=rates_azn,
        cross_rates=cross_matrix,
    )


@router.post("/convert", response_model=CurrencyConversionResponse)
async def convert_currency_amount(payload: CurrencyConversionRequest):
    """Converts amount between two currencies with optional safety margin cushion."""
    converted = convert_amount(
        amount=payload.amount,
        from_currency=payload.from_currency,
        to_currency=payload.to_currency,
        safety_buffer_pct=payload.safety_buffer_pct,
    )
    exchange_rate = float(get_exchange_rate(payload.from_currency, payload.to_currency))
    major_breakdown = convert_to_all_major(payload.amount, payload.from_currency)

    return CurrencyConversionResponse(
        amount=payload.amount,
        from_currency=payload.from_currency,
        to_currency=payload.to_currency,
        exchange_rate=round(exchange_rate, 4),
        converted_amount=float(converted),
        converted_all_major=major_breakdown,
    )


@router.post("/germany", response_model=GermanyProofOfFundsResponse)
async def simulate_germany_finances(payload: GermanyCalcRequest):
    """Calculates Germany § 16b AufenthG Sperrkonto (Blocked Account) & total first-year liquidity."""
    res = calculate_germany_funds(
        months=payload.months,
        city_tier=payload.city_tier,
        tuition_fee_eur=payload.tuition_fee_eur,
        include_arrival_buffer=payload.include_arrival_buffer,
        exchange_safety_buffer_pct=payload.exchange_safety_buffer_pct,
    )
    return GermanyProofOfFundsResponse(
        country=res.country,
        statutory_monthly_amount=res.statutory_monthly_amount,
        number_of_months=res.number_of_months,
        blocked_account_total=res.blocked_account_total,
        account_setup_fee=res.account_setup_fee,
        account_buffer_deposit=res.account_buffer_deposit,
        total_blocked_deposit_required=res.total_blocked_deposit_required,
        health_insurance_annual=res.health_insurance_annual,
        semester_contributions_annual=res.semester_contributions_annual,
        visa_fee=res.visa_fee,
        estimated_arrival_buffer=res.estimated_arrival_buffer,
        total_first_year_liquidity_eur=res.total_first_year_liquidity_eur,
        total_first_year_liquidity_azn=res.total_first_year_liquidity_azn,
        total_in_all_currencies=res.total_in_all_currencies,
        city_tier=res.city_tier,
        estimated_monthly_realistic_cost=res.estimated_monthly_realistic_cost,
        monthly_statutory_shortfall=res.monthly_statutory_shortfall,
        statutory_note=res.statutory_note,
        breakdown=res.breakdown,
    )


@router.post("/uk", response_model=UKProofOfFundsResponse)
async def simulate_uk_finances(payload: UKCalcRequest):
    """Calculates UKVI Appendix Student visa maintenance requirement and 28-day holding total."""
    res = calculate_uk_funds(
        location_type=payload.location_type,
        course_tuition_annual_gbp=payload.course_tuition_annual_gbp,
        deposit_paid_to_cas_gbp=payload.deposit_paid_to_cas_gbp,
        course_duration_months=payload.course_duration_months,
        exchange_safety_buffer_pct=payload.exchange_safety_buffer_pct,
    )
    return UKProofOfFundsResponse(
        country=res.country,
        location_type=res.location_type,
        maintenance_monthly_rate_gbp=res.maintenance_monthly_rate_gbp,
        maintenance_months_assessed=res.maintenance_months_assessed,
        maintenance_total_gbp=res.maintenance_total_gbp,
        course_tuition_annual_gbp=res.course_tuition_annual_gbp,
        deposit_paid_to_cas_gbp=res.deposit_paid_to_cas_gbp,
        outstanding_tuition_gbp=res.outstanding_tuition_gbp,
        immigration_health_surcharge_gbp=res.immigration_health_surcharge_gbp,
        visa_fee_gbp=res.visa_fee_gbp,
        flight_and_settling_buffer_gbp=res.flight_and_settling_buffer_gbp,
        total_funds_to_hold_28_days_gbp=res.total_funds_to_hold_28_days_gbp,
        total_funds_in_azn=res.total_funds_in_azn,
        total_in_all_currencies=res.total_in_all_currencies,
        holding_rule_statement=res.holding_rule_statement,
        breakdown=res.breakdown,
    )


@router.post("/usa", response_model=USProofOfFundsResponse)
async def simulate_usa_finances(payload: USCalcRequest):
    """Calculates US Form I-20 Cost of Attendance (COA) and consular affidavit liquid requirements."""
    res = calculate_us_funds(
        tuition_annual_usd=payload.tuition_annual_usd,
        institutional_fees_usd=payload.institutional_fees_usd,
        location_tier=payload.location_tier,
        scholarship_award_usd=payload.scholarship_award_usd,
        exchange_safety_buffer_pct=payload.exchange_safety_buffer_pct,
    )
    return USProofOfFundsResponse(
        country=res.country,
        tuition_annual_usd=res.tuition_annual_usd,
        mandatory_institutional_fees_usd=res.mandatory_institutional_fees_usd,
        living_room_and_board_usd=res.living_room_and_board_usd,
        health_insurance_usd=res.health_insurance_usd,
        books_and_supplies_usd=res.books_and_supplies_usd,
        personal_and_transport_usd=res.personal_and_transport_usd,
        official_i20_total_usd=res.official_i20_total_usd,
        sevis_fee_usd=res.sevis_fee_usd,
        mrv_visa_fee_usd=res.mrv_visa_fee_usd,
        recommended_consular_buffer_usd=res.recommended_consular_buffer_usd,
        total_recommended_affidavit_usd=res.total_recommended_affidavit_usd,
        total_in_azn=res.total_in_azn,
        total_in_all_currencies=res.total_in_all_currencies,
        consular_advice=res.consular_advice,
        breakdown=res.breakdown,
    )


@router.post("/italy", response_model=ItalyProofOfFundsResponse)
async def simulate_italy_finances(payload: ItalyCalcRequest):
    """Calculates Italian ISEE-U (Equivalent Economic Situation) and regional DSU scholarship entitlement."""
    res = calculate_italy_funds(
        family_members_count=payload.family_members_count,
        family_annual_income_azn=payload.family_annual_income_azn,
        real_estate_abroad_azn=payload.real_estate_abroad_azn,
        city_tier=payload.city_tier,
        base_tuition_eur=payload.base_tuition_eur,
        exchange_safety_buffer_pct=payload.exchange_safety_buffer_pct,
    )
    return ItalyProofOfFundsResponse(
        country=res.country,
        calculated_isee_parificato_eur=res.calculated_isee_parificato_eur,
        qualifies_for_dsu_fee_waiver=res.qualifies_for_dsu_fee_waiver,
        qualifies_for_dsu_cash_stipend=res.qualifies_for_dsu_cash_stipend,
        estimated_dsu_cash_stipend_eur=res.estimated_dsu_cash_stipend_eur,
        annual_tuition_after_dsu_eur=res.annual_tuition_after_dsu_eur,
        monthly_living_cost_eur=res.monthly_living_cost_eur,
        annual_living_cost_eur=res.annual_living_cost_eur,
        permesso_di_soggiorno_fee_eur=res.permesso_di_soggiorno_fee_eur,
        ssn_health_insurance_eur=res.ssn_health_insurance_eur,
        net_first_year_cost_eur=res.net_first_year_cost_eur,
        net_first_year_cost_azn=res.net_first_year_cost_azn,
        total_in_all_currencies=res.total_in_all_currencies,
        dsu_eligibility_verdict=res.dsu_eligibility_verdict,
        breakdown=res.breakdown,
    )


@router.post("/compare", response_model=DestinationCompareResponse)
async def compare_study_destinations(payload: DestinationCompareRequest):
    """Benchmarks statutory visa liquidity requirements across Germany, UK, US, and Italy against student budget."""
    res = compare_study_destinations_finance(
        student_annual_budget_azn=payload.student_annual_budget_azn,
        tuition_eur=payload.tuition_eur,
        tuition_gbp=payload.tuition_gbp,
        tuition_usd=payload.tuition_usd,
        tuition_italy_eur=payload.tuition_italy_eur,
        family_members_count=payload.family_members_count,
        family_income_azn=payload.family_income_azn,
    )
    return DestinationCompareResponse(
        student_budget_azn=res.student_budget_azn,
        destinations=[DestinationComparisonItem(**d) for d in res.destinations],
        most_affordable_country=res.most_affordable_country,
        highest_liquidity_country=res.highest_liquidity_country,
        summary_verdict=res.summary_verdict,
    )
