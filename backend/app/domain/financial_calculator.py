"""Financial calculations domain for student visas, blocked accounts, and living costs.

Implements official statutory visa proof-of-funds rules, blocked accounts (Sperrkonto),
CAS maintenance funds, I-20 Cost of Attendance (COA), and Italian ISEE-U/DSU models,
with multi-currency conversion to Azerbaijani Manat (AZN) and major study-abroad currencies.

Statutory and Regulatory References:
- Germany: § 16b AufenthG & Federal Foreign Office (Auswärtiges Amt) standard rate (€11,904 / €992/mo).
- UK: UK Visas and Immigration (UKVI) Appendix Student maintenance rules (London: £1,334/mo; Outer: £1,023/mo, max 9 months).
- US: 8 CFR 214.2(f)(1)(i)(B) - I-20 full-year liquid funding demonstration + SEVIS I-901 + DS-160 fees.
- Italy: D.P.C.M. 159/2013 & D.Lgs. 68/2012 (ISEE Parificato threshold €25,000 for DSU grants).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List


class Currency(str, Enum):
    AZN = "AZN"
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    TRY = "TRY"
    PLN = "PLN"
    HUF = "HUF"


class GermanCityTier(str, Enum):
    TIER_1_EXPENSIVE = "tier_1_expensive"  # Munich, Frankfurt, Stuttgart
    TIER_2_MODERATE = "tier_2_moderate"    # Berlin, Hamburg, Cologne, Heidelberg
    TIER_3_AFFORDABLE = "tier_3_affordable"# Leipzig, Dresden, Bremen, Clausthal, Ilmenau


class UKLocationType(str, Enum):
    INNER_LONDON = "inner_london"
    OUTER_LONDON = "outer_london"
    OUTSIDE_LONDON = "outside_london"


class USLivingLocationTier(str, Enum):
    METROPOLITAN_HIGH = "metropolitan_high"      # NYC, San Francisco, Boston, LA
    SUBURBAN_MODERATE = "suburban_moderate"      # Austin, Chicago, Pittsburgh, Atlanta
    COLLEGE_TOWN_LOW = "college_town_low"        # Urbana-Champaign, Ann Arbor, West Lafayette


class ItalyCityTier(str, Enum):
    TIER_1_METROPOLITAN = "tier_1_metropolitan"  # Milan, Rome
    TIER_2_MAJOR_STUDENT = "tier_2_major_student"# Bologna, Turin, Florence
    TIER_3_REGIONAL = "tier_3_regional"          # Padua, Pisa, Siena, Genoa
    TIER_4_SOUTHERN = "tier_4_southern"          # Naples, Bari, Messina, Palermo


# Baseline Central Bank of Azerbaijan (CBAR) reference rates against AZN
EXCHANGE_RATES_TO_AZN: Dict[Currency, Decimal] = {
    Currency.AZN: Decimal("1.0000"),
    Currency.USD: Decimal("1.7000"),
    Currency.EUR: Decimal("1.8540"),
    Currency.GBP: Decimal("2.2180"),
    Currency.TRY: Decimal("0.0495"),
    Currency.PLN: Decimal("0.4320"),
    Currency.HUF: Decimal("0.0047"),
}


def round_currency(value: Decimal) -> Decimal:
    """Rounds currency to two decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_exchange_rate(from_currency: Currency, to_currency: Currency) -> Decimal:
    """Returns exchange rate from one currency to another using AZN base."""
    rate_from_to_azn = EXCHANGE_RATES_TO_AZN[from_currency]
    rate_to_to_azn = EXCHANGE_RATES_TO_AZN[to_currency]
    return rate_from_to_azn / rate_to_to_azn


def convert_amount(
    amount: Decimal | float | int,
    from_currency: Currency,
    to_currency: Currency,
    safety_buffer_pct: float = 0.0,
) -> Decimal:
    """Converts amount from one currency to another with optional safety margin cushion."""
    dec_amount = Decimal(str(amount))
    rate = get_exchange_rate(from_currency, to_currency)
    converted = dec_amount * rate
    if safety_buffer_pct > 0.0:
        buffer_mult = Decimal("1.0") + (Decimal(str(safety_buffer_pct)) / Decimal("100.0"))
        converted = converted * buffer_mult
    return round_currency(converted)


def convert_to_all_major(amount: Decimal | float | int, from_currency: Currency) -> Dict[str, float]:
    """Provides breakdown in all 4 primary reporting currencies (AZN, EUR, USD, GBP)."""
    return {
        Currency.AZN.value: float(convert_amount(amount, from_currency, Currency.AZN)),
        Currency.EUR.value: float(convert_amount(amount, from_currency, Currency.EUR)),
        Currency.USD.value: float(convert_amount(amount, from_currency, Currency.USD)),
        Currency.GBP.value: float(convert_amount(amount, from_currency, Currency.GBP)),
    }


# ==============================================================================
# GERMANY SPERRKONTO & PROOF OF FUNDS
# ==============================================================================

GERMANY_STATUTORY_MONTHLY_EUR = Decimal("992.00")
GERMANY_STANDARD_MONTHS = 12
GERMANY_HEALTH_INSURANCE_MONTHLY_EUR = Decimal("128.50")  # TK/Barmer/AOK statutory public insurance
GERMANY_SEMESTER_FEE_EUR = Decimal("310.00")              # University contribution + public transit pass
GERMANY_VISA_FEE_EUR = Decimal("75.00")                   # National Visa Type D
GERMANY_PROVIDER_SETUP_FEE_EUR = Decimal("89.00")         # Expatrio / Fintiba opening fee
GERMANY_PROVIDER_BUFFER_EUR = Decimal("100.00")           # Minimum buffer deposit required by providers


@dataclass
class GermanyProofOfFundsResult:
    country: str = "Germany"
    statutory_monthly_amount: float = 0.0
    number_of_months: int = 12
    blocked_account_total: float = 0.0
    account_setup_fee: float = 0.0
    account_buffer_deposit: float = 0.0
    total_blocked_deposit_required: float = 0.0
    health_insurance_annual: float = 0.0
    semester_contributions_annual: float = 0.0
    visa_fee: float = 0.0
    estimated_arrival_buffer: float = 0.0
    total_first_year_liquidity_eur: float = 0.0
    total_first_year_liquidity_azn: float = 0.0
    total_in_all_currencies: Dict[str, float] = field(default_factory=dict)
    city_tier: str = GermanCityTier.TIER_2_MODERATE.value
    estimated_monthly_realistic_cost: float = 0.0
    monthly_statutory_shortfall: float = 0.0
    statutory_note: str = ""
    breakdown: Dict[str, float] = field(default_factory=dict)


def calculate_germany_funds(
    months: int = 12,
    city_tier: GermanCityTier = GermanCityTier.TIER_2_MODERATE,
    tuition_fee_eur: float = 0.0,
    include_arrival_buffer: bool = True,
    exchange_safety_buffer_pct: float = 3.0,
) -> GermanyProofOfFundsResult:
    """Calculates official German Blocked Account (Sperrkonto) and first-year cashflow requirements.

    Args:
        months: Duration in months (standard is 12 for 1 academic year).
        city_tier: Living expense tier by city.
        tuition_fee_eur: Public universities are €0, some private or Baden-Württemberg charge €1,500/sem.
        include_arrival_buffer: Rental deposit (Kaution ~2 months) and initial setup items.
        exchange_safety_buffer_pct: FX rate safety buffer percentage.
    """
    if months < 1:
        months = 12

    dec_months = Decimal(str(months))
    blocked_base = round_currency(GERMANY_STATUTORY_MONTHLY_EUR * dec_months)
    setup_fee = GERMANY_PROVIDER_SETUP_FEE_EUR
    provider_buffer = GERMANY_PROVIDER_BUFFER_EUR
    total_blocked_deposit = round_currency(blocked_base + setup_fee + provider_buffer)

    health_insurance_annual = round_currency(GERMANY_HEALTH_INSURANCE_MONTHLY_EUR * dec_months)
    semesters = (months + 5) // 6
    semester_contributions = round_currency(GERMANY_SEMESTER_FEE_EUR * Decimal(str(semesters)))
    visa_fee = GERMANY_VISA_FEE_EUR
    tuition = Decimal(str(max(0.0, tuition_fee_eur)))

    tier_multipliers = {
        GermanCityTier.TIER_1_EXPENSIVE: Decimal("1.18"),
        GermanCityTier.TIER_2_MODERATE: Decimal("1.00"),
        GermanCityTier.TIER_3_AFFORDABLE: Decimal("0.88"),
    }
    multiplier = tier_multipliers.get(city_tier, Decimal("1.00"))
    realistic_monthly = round_currency(GERMANY_STATUTORY_MONTHLY_EUR * multiplier)
    monthly_shortfall = round_currency(max(Decimal("0.00"), realistic_monthly - GERMANY_STATUTORY_MONTHLY_EUR))

    arrival_buffer = Decimal("1200.00") if include_arrival_buffer else Decimal("0.00")

    total_eur = round_currency(
        total_blocked_deposit
        + health_insurance_annual
        + semester_contributions
        + visa_fee
        + tuition
        + arrival_buffer
    )

    total_azn = convert_amount(total_eur, Currency.EUR, Currency.AZN, exchange_safety_buffer_pct)

    note = (
        f"Statutory Sperrkonto base is €{GERMANY_STATUTORY_MONTHLY_EUR} per month (€{blocked_base:,.2f} for {months} months). "
        "Provider opening fees (€89) and emergency deposit (€100) are included in the transfer request."
    )
    if monthly_shortfall > 0:
        note += f" In {city_tier.value.replace('_', ' ')}, actual monthly expenses average €{realistic_monthly:,.2f}, leaving a €{monthly_shortfall:,.2f}/mo gap."

    breakdown = {
        "blocked_account_base_eur": float(blocked_base),
        "provider_setup_and_buffer_eur": float(setup_fee + provider_buffer),
        "health_insurance_eur": float(health_insurance_annual),
        "semester_contributions_eur": float(semester_contributions),
        "tuition_fees_eur": float(tuition),
        "arrival_rental_deposit_eur": float(arrival_buffer),
        "visa_fee_eur": float(visa_fee),
    }

    return GermanyProofOfFundsResult(
        statutory_monthly_amount=float(GERMANY_STATUTORY_MONTHLY_EUR),
        number_of_months=months,
        blocked_account_total=float(blocked_base),
        account_setup_fee=float(setup_fee),
        account_buffer_deposit=float(provider_buffer),
        total_blocked_deposit_required=float(total_blocked_deposit),
        health_insurance_annual=float(health_insurance_annual),
        semester_contributions_annual=float(semester_contributions),
        visa_fee=float(visa_fee),
        estimated_arrival_buffer=float(arrival_buffer),
        total_first_year_liquidity_eur=float(total_eur),
        total_first_year_liquidity_azn=float(total_azn),
        total_in_all_currencies=convert_to_all_major(total_eur, Currency.EUR),
        city_tier=city_tier.value,
        estimated_monthly_realistic_cost=float(realistic_monthly),
        monthly_statutory_shortfall=float(monthly_shortfall),
        statutory_note=note,
        breakdown=breakdown,
    )


# ==============================================================================
# UK CAS PROOF OF FUNDS & MAINTENANCE
# ==============================================================================

UKVI_LONDON_MONTHLY_GBP = Decimal("1334.00")
UKVI_OUTSIDE_LONDON_MONTHLY_GBP = Decimal("1023.00")
UKVI_MAX_MAINTENANCE_MONTHS = 9
UKVI_IHS_ANNUAL_FEE_GBP = Decimal("776.00")
UKVI_VISA_APPLICATION_FEE_GBP = Decimal("490.00")


@dataclass
class UKProofOfFundsResult:
    country: str = "United Kingdom"
    location_type: str = UKLocationType.OUTSIDE_LONDON.value
    maintenance_monthly_rate_gbp: float = 0.0
    maintenance_months_assessed: int = 9
    maintenance_total_gbp: float = 0.0
    course_tuition_annual_gbp: float = 0.0
    deposit_paid_to_cas_gbp: float = 0.0
    outstanding_tuition_gbp: float = 0.0
    immigration_health_surcharge_gbp: float = 0.0
    visa_fee_gbp: float = 0.0
    flight_and_settling_buffer_gbp: float = 0.0
    total_funds_to_hold_28_days_gbp: float = 0.0
    total_funds_in_azn: float = 0.0
    total_in_all_currencies: Dict[str, float] = field(default_factory=dict)
    holding_rule_statement: str = ""
    breakdown: Dict[str, float] = field(default_factory=dict)


def calculate_uk_funds(
    location_type: UKLocationType = UKLocationType.OUTSIDE_LONDON,
    course_tuition_annual_gbp: float = 18500.0,
    deposit_paid_to_cas_gbp: float = 2000.0,
    course_duration_months: int = 9,
    exchange_safety_buffer_pct: float = 3.0,
) -> UKProofOfFundsResult:
    """Calculates UKVI Appendix Student visa maintenance requirement and 28-day holding total.

    Args:
        location_type: Inner/Outer London vs Outside London.
        course_tuition_annual_gbp: First year tuition fee quoted on CAS.
        deposit_paid_to_cas_gbp: Deposit formally logged on CAS statement.
        course_duration_months: Number of months of the course (capped at 9 for maintenance).
        exchange_safety_buffer_pct: FX rate safety buffer percentage.
    """
    assessed_months = min(max(1, course_duration_months), UKVI_MAX_MAINTENANCE_MONTHS)
    monthly_rate = (
        UKVI_LONDON_MONTHLY_GBP
        if location_type in (UKLocationType.INNER_LONDON, UKLocationType.OUTER_LONDON)
        else UKVI_OUTSIDE_LONDON_MONTHLY_GBP
    )

    maintenance_total = round_currency(monthly_rate * Decimal(str(assessed_months)))
    tuition = Decimal(str(max(0.0, course_tuition_annual_gbp)))
    deposit = Decimal(str(max(0.0, min(tuition, Decimal(str(deposit_paid_to_cas_gbp))))))
    outstanding_tuition = round_currency(tuition - deposit)

    ihs_fee = UKVI_IHS_ANNUAL_FEE_GBP
    visa_fee = UKVI_VISA_APPLICATION_FEE_GBP
    settling_buffer = Decimal("800.00")

    strict_28_day_bank_holding = round_currency(maintenance_total + outstanding_tuition)
    total_gbp = round_currency(strict_28_day_bank_holding + ihs_fee + visa_fee + settling_buffer)
    total_azn = convert_amount(total_gbp, Currency.GBP, Currency.AZN, exchange_safety_buffer_pct)

    holding_rule = (
        f"UKVI strictly requires £{strict_28_day_bank_holding:,.2f} (£{maintenance_total:,.2f} maintenance + "
        f"£{outstanding_tuition:,.2f} outstanding tuition) to be held continuously in your or your parents' bank account "
        "for at least 28 consecutive days ending no more than 31 days before your visa application date. "
        "The balance must not drop below this figure for even a single day."
    )

    breakdown = {
        "monthly_maintenance_rate_gbp": float(monthly_rate),
        "maintenance_total_gbp": float(maintenance_total),
        "outstanding_tuition_gbp": float(outstanding_tuition),
        "immigration_health_surcharge_gbp": float(ihs_fee),
        "visa_application_fee_gbp": float(visa_fee),
        "flight_and_settling_buffer_gbp": float(settling_buffer),
        "strict_28_day_bank_statement_requirement_gbp": float(strict_28_day_bank_holding),
    }

    return UKProofOfFundsResult(
        location_type=location_type.value,
        maintenance_monthly_rate_gbp=float(monthly_rate),
        maintenance_months_assessed=assessed_months,
        maintenance_total_gbp=float(maintenance_total),
        course_tuition_annual_gbp=float(tuition),
        deposit_paid_to_cas_gbp=float(deposit),
        outstanding_tuition_gbp=float(outstanding_tuition),
        immigration_health_surcharge_gbp=float(ihs_fee),
        visa_fee_gbp=float(visa_fee),
        flight_and_settling_buffer_gbp=float(settling_buffer),
        total_funds_to_hold_28_days_gbp=float(total_gbp),
        total_funds_in_azn=float(total_azn),
        total_in_all_currencies=convert_to_all_major(total_gbp, Currency.GBP),
        holding_rule_statement=holding_rule,
        breakdown=breakdown,
    )


# ==============================================================================
# US I-20 COST OF ATTENDANCE & F-1 AFFIDAVIT
# ==============================================================================

US_SEVIS_FEE_USD = Decimal("350.00")
US_DS160_VISA_FEE_USD = Decimal("185.00")


@dataclass
class USProofOfFundsResult:
    country: str = "United States"
    tuition_annual_usd: float = 0.0
    mandatory_institutional_fees_usd: float = 0.0
    living_room_and_board_usd: float = 0.0
    health_insurance_usd: float = 0.0
    books_and_supplies_usd: float = 0.0
    personal_and_transport_usd: float = 0.0
    official_i20_total_usd: float = 0.0
    sevis_fee_usd: float = 350.0
    mrv_visa_fee_usd: float = 185.0
    recommended_consular_buffer_usd: float = 0.0
    total_recommended_affidavit_usd: float = 0.0
    total_in_azn: float = 0.0
    total_in_all_currencies: Dict[str, float] = field(default_factory=dict)
    consular_advice: str = ""
    breakdown: Dict[str, float] = field(default_factory=dict)


def calculate_us_funds(
    tuition_annual_usd: float = 28000.0,
    institutional_fees_usd: float = 1800.0,
    location_tier: USLivingLocationTier = USLivingLocationTier.SUBURBAN_MODERATE,
    scholarship_award_usd: float = 0.0,
    exchange_safety_buffer_pct: float = 3.0,
) -> USProofOfFundsResult:
    """Calculates official US Form I-20 Cost of Attendance (COA) and consular affidavit liquid requirements.

    Args:
        tuition_annual_usd: Academic year tuition stated by university.
        institutional_fees_usd: Campus technology, recreation, and laboratory fees.
        location_tier: Location tier determining room & board.
        scholarship_award_usd: Documented institutional scholarship deducting from net requirement.
        exchange_safety_buffer_pct: FX rate safety buffer percentage.
    """
    living_rates = {
        USLivingLocationTier.METROPOLITAN_HIGH: Decimal("22500.00"),
        USLivingLocationTier.SUBURBAN_MODERATE: Decimal("16500.00"),
        USLivingLocationTier.COLLEGE_TOWN_LOW: Decimal("12500.00"),
    }
    living_room_board = living_rates.get(location_tier, Decimal("16500.00"))
    health_insurance = Decimal("2400.00")
    books = Decimal("1200.00")
    personal = Decimal("2200.00")

    tuition = Decimal(str(max(0.0, tuition_annual_usd)))
    fees = Decimal(str(max(0.0, institutional_fees_usd)))
    scholarship = Decimal(str(max(0.0, scholarship_award_usd)))

    gross_i20 = tuition + fees + living_room_board + health_insurance + books + personal
    net_i20 = round_currency(max(Decimal("0.00"), gross_i20 - scholarship))

    sevis_fee = US_SEVIS_FEE_USD
    mrv_visa_fee = US_DS160_VISA_FEE_USD

    consular_buffer = round_currency(net_i20 * Decimal("0.15"))
    total_affidavit = round_currency(net_i20 + sevis_fee + mrv_visa_fee + consular_buffer)
    total_azn = convert_amount(total_affidavit, Currency.USD, Currency.AZN, exchange_safety_buffer_pct)

    advice = (
        f"Your official Form I-20 will specify ${net_i20:,.2f} as the required minimum first-year funding "
        f"(gross ${gross_i20:,.2f} minus ${scholarship:,.2f} scholarship). "
        "At the US Embassy consular interview in Baku, officers require proof that these funds are readily liquid "
        f"(bank deposits, not immovable property). We recommend demonstrating at least ${total_affidavit:,.2f} "
        "to satisfy consular officer discretion."
    )

    breakdown = {
        "tuition_usd": float(tuition),
        "mandatory_fees_usd": float(fees),
        "room_and_board_usd": float(living_room_board),
        "health_insurance_usd": float(health_insurance),
        "books_and_supplies_usd": float(books),
        "personal_expenses_usd": float(personal),
        "scholarship_deduction_usd": float(scholarship),
        "official_net_i20_usd": float(net_i20),
        "sevis_fee_usd": float(sevis_fee),
        "mrv_visa_fee_usd": float(mrv_visa_fee),
        "consular_safety_buffer_usd": float(consular_buffer),
    }

    return USProofOfFundsResult(
        tuition_annual_usd=float(tuition),
        mandatory_institutional_fees_usd=float(fees),
        living_room_and_board_usd=float(living_room_board),
        health_insurance_usd=float(health_insurance),
        books_and_supplies_usd=float(books),
        personal_and_transport_usd=float(personal),
        official_i20_total_usd=float(net_i20),
        sevis_fee_usd=float(sevis_fee),
        mrv_visa_fee_usd=float(mrv_visa_fee),
        recommended_consular_buffer_usd=float(consular_buffer),
        total_recommended_affidavit_usd=float(total_affidavit),
        total_in_azn=float(total_azn),
        total_in_all_currencies=convert_to_all_major(total_affidavit, Currency.USD),
        consular_advice=advice,
        breakdown=breakdown,
    )


# ==============================================================================
# ITALY ISEE-U & REGIONAL DSU SCHOLARSHIP ESTIMATOR
# ==============================================================================

ISEE_MAX_DSU_THRESHOLD_EUR = Decimal("25000.00")
ISEE_TOP_BRACKET_THRESHOLD_EUR = Decimal("15000.00")
ITALY_PERMESSO_FEE_EUR = Decimal("118.00")
ITALY_SSN_STUDENT_ANNUAL_EUR = Decimal("700.00")


@dataclass
class ItalyProofOfFundsResult:
    country: str = "Italy"
    calculated_isee_parificato_eur: float = 0.0
    qualifies_for_dsu_fee_waiver: bool = False
    qualifies_for_dsu_cash_stipend: bool = False
    estimated_dsu_cash_stipend_eur: float = 0.0
    annual_tuition_after_dsu_eur: float = 0.0
    monthly_living_cost_eur: float = 0.0
    annual_living_cost_eur: float = 0.0
    permesso_di_soggiorno_fee_eur: float = 118.0
    ssn_health_insurance_eur: float = 700.0
    net_first_year_cost_eur: float = 0.0
    net_first_year_cost_azn: float = 0.0
    total_in_all_currencies: Dict[str, float] = field(default_factory=dict)
    dsu_eligibility_verdict: str = ""
    breakdown: Dict[str, float] = field(default_factory=dict)


def calculate_italy_funds(
    family_members_count: int = 4,
    family_annual_income_azn: float = 24000.0,
    real_estate_abroad_azn: float = 80000.0,
    city_tier: ItalyCityTier = ItalyCityTier.TIER_2_MAJOR_STUDENT,
    base_tuition_eur: float = 3500.0,
    exchange_safety_buffer_pct: float = 3.0,
) -> ItalyProofOfFundsResult:
    """Calculates Italian ISEE-U (Equivalent Economic Situation) and regional DSU scholarship entitlement.

    Args:
        family_members_count: Total nuclear family members sharing household.
        family_annual_income_azn: Total gross annual household income in Azerbaijan.
        real_estate_abroad_azn: Total market value of residential properties owned by family.
        city_tier: City location tier determining rental costs.
        base_tuition_eur: Standard university tuition fee prior to DSU waiver.
        exchange_safety_buffer_pct: FX rate safety buffer percentage.
    """
    scale_factors = {
        1: Decimal("1.00"),
        2: Decimal("1.57"),
        3: Decimal("2.04"),
        4: Decimal("2.46"),
        5: Decimal("2.85"),
    }
    equiv_scale = scale_factors.get(
        family_members_count,
        Decimal("2.85") + Decimal(str(max(0, family_members_count - 5))) * Decimal("0.35"),
    )

    income_eur = convert_amount(family_annual_income_azn, Currency.AZN, Currency.EUR)
    property_eur = convert_amount(real_estate_abroad_azn, Currency.AZN, Currency.EUR)

    property_allowance = Decimal("52500.00")
    net_property = max(Decimal("0.00"), property_eur - property_allowance)
    patrimony_component = net_property * Decimal("0.20")

    ise_total = income_eur + patrimony_component
    isee_parificato = round_currency(ise_total / equiv_scale)

    qualifies_dsu = isee_parificato <= ISEE_MAX_DSU_THRESHOLD_EUR
    qualifies_top_stipend = isee_parificato <= ISEE_TOP_BRACKET_THRESHOLD_EUR

    if qualifies_dsu:
        tuition_after_dsu = Decimal("156.00")
        stipend_eur = Decimal("7200.00") if qualifies_top_stipend else Decimal("4500.00")
    else:
        tuition_after_dsu = Decimal(str(base_tuition_eur))
        stipend_eur = Decimal("0.00")

    monthly_rates = {
        ItalyCityTier.TIER_1_METROPOLITAN: Decimal("950.00"),
        ItalyCityTier.TIER_2_MAJOR_STUDENT: Decimal("780.00"),
        ItalyCityTier.TIER_3_REGIONAL: Decimal("620.00"),
        ItalyCityTier.TIER_4_SOUTHERN: Decimal("480.00"),
    }
    monthly_living = monthly_rates.get(city_tier, Decimal("780.00"))
    annual_living = round_currency(monthly_living * Decimal("12.0"))

    permesso_fee = ITALY_PERMESSO_FEE_EUR
    ssn_health = ITALY_SSN_STUDENT_ANNUAL_EUR

    gross_cost = tuition_after_dsu + annual_living + permesso_fee + ssn_health
    net_cost = round_currency(max(Decimal("0.00"), gross_cost - stipend_eur))
    net_azn = convert_amount(net_cost, Currency.EUR, Currency.AZN, exchange_safety_buffer_pct)

    if qualifies_dsu:
        verdict = (
            f"Your calculated ISEE Parificato of €{isee_parificato:,.2f} is BELOW the €{ISEE_MAX_DSU_THRESHOLD_EUR:,.2f} threshold. "
            f"You qualify for 100% university tuition exemption (saving €{float(base_tuition_eur) - 156:,.2f}) plus "
            f"an estimated regional cash scholarship stipend of €{stipend_eur:,.2f}/year, free cafeteria meals, and subsidized student housing."
        )
    else:
        verdict = (
            f"Your calculated ISEE Parificato of €{isee_parificato:,.2f} exceeds the €{ISEE_MAX_DSU_THRESHOLD_EUR:,.2f} ceiling. "
            "You will be placed in an intermediate tuition bracket and are self-funded for accommodation."
        )

    breakdown = {
        "family_income_eur": float(income_eur),
        "property_valuation_eur": float(property_eur),
        "equivalence_scale_factor": float(equiv_scale),
        "calculated_isee_parificato_eur": float(isee_parificato),
        "tuition_payable_eur": float(tuition_after_dsu),
        "annual_living_cost_eur": float(annual_living),
        "dsu_scholarship_stipend_eur": float(stipend_eur),
        "permesso_fee_eur": float(permesso_fee),
        "ssn_health_insurance_eur": float(ssn_health),
    }

    return ItalyProofOfFundsResult(
        calculated_isee_parificato_eur=float(isee_parificato),
        qualifies_for_dsu_fee_waiver=qualifies_dsu,
        qualifies_for_dsu_cash_stipend=qualifies_dsu,
        estimated_dsu_cash_stipend_eur=float(stipend_eur),
        annual_tuition_after_dsu_eur=float(tuition_after_dsu),
        monthly_living_cost_eur=float(monthly_living),
        annual_living_cost_eur=float(annual_living),
        permesso_di_soggiorno_fee_eur=float(permesso_fee),
        ssn_health_insurance_eur=float(ssn_health),
        net_first_year_cost_eur=float(net_cost),
        net_first_year_cost_azn=float(net_azn),
        total_in_all_currencies=convert_to_all_major(net_cost, Currency.EUR),
        dsu_eligibility_verdict=verdict,
        breakdown=breakdown,
    )


# ==============================================================================
# MULTI-COUNTRY COMPARATIVE BENCHMARK
# ==============================================================================

@dataclass
class DestinationComparisonResult:
    student_budget_azn: float
    destinations: List[Dict[str, Any]]
    most_affordable_country: str
    highest_liquidity_country: str
    summary_verdict: str


def compare_study_destinations_finance(
    student_annual_budget_azn: float = 35000.0,
    tuition_eur: float = 0.0,
    tuition_gbp: float = 18000.0,
    tuition_usd: float = 28000.0,
    tuition_italy_eur: float = 3500.0,
    family_members_count: int = 4,
    family_income_azn: float = 24000.0,
) -> DestinationComparisonResult:
    """Compares statutory visa liquidity and first-year living costs across Germany, UK, US, and Italy."""
    budget = Decimal(str(student_annual_budget_azn))

    de_res = calculate_germany_funds(months=12, tuition_fee_eur=tuition_eur)
    uk_res = calculate_uk_funds(location_type=UKLocationType.OUTSIDE_LONDON, course_tuition_annual_gbp=tuition_gbp)
    us_res = calculate_us_funds(tuition_annual_usd=tuition_usd)
    it_res = calculate_italy_funds(
        family_members_count=family_members_count,
        family_annual_income_azn=family_income_azn,
        base_tuition_eur=tuition_italy_eur,
    )

    dest_list: List[Dict[str, Any]] = [
        {
            "country": "Germany",
            "currency": "EUR",
            "visa_category": "Sperrkonto (Blocked Account § 16b)",
            "statutory_deposit_native": de_res.total_blocked_deposit_required,
            "total_first_year_cost_native": de_res.total_first_year_liquidity_eur,
            "total_first_year_cost_azn": de_res.total_first_year_liquidity_azn,
            "is_within_budget": budget >= Decimal(str(de_res.total_first_year_liquidity_azn)),
            "budget_delta_azn": float(budget - Decimal(str(de_res.total_first_year_liquidity_azn))),
            "key_regulatory_condition": "€11,904 blocked in account before visa interview.",
        },
        {
            "country": "United Kingdom",
            "currency": "GBP",
            "visa_category": "CAS Maintenance (Appendix Student)",
            "statutory_deposit_native": uk_res.total_funds_to_hold_28_days_gbp,
            "total_first_year_cost_native": uk_res.total_funds_to_hold_28_days_gbp,
            "total_first_year_cost_azn": uk_res.total_funds_in_azn,
            "is_within_budget": budget >= Decimal(str(uk_res.total_funds_in_azn)),
            "budget_delta_azn": float(budget - Decimal(str(uk_res.total_funds_in_azn))),
            "key_regulatory_condition": "Funds must be held in bank account for 28 consecutive days.",
        },
        {
            "country": "United States",
            "currency": "USD",
            "visa_category": "Form I-20 Full Cost Affidavit (F-1)",
            "statutory_deposit_native": us_res.official_i20_total_usd,
            "total_first_year_cost_native": us_res.total_recommended_affidavit_usd,
            "total_first_year_cost_azn": us_res.total_in_azn,
            "is_within_budget": budget >= Decimal(str(us_res.total_in_azn)),
            "budget_delta_azn": float(budget - Decimal(str(us_res.total_in_azn))),
            "key_regulatory_condition": "Official I-20 proof of liquid funds for full 1st academic year.",
        },
        {
            "country": "Italy",
            "currency": "EUR",
            "visa_category": "ISEE-U / Regional DSU Grant",
            "statutory_deposit_native": it_res.net_first_year_cost_eur,
            "total_first_year_cost_native": it_res.net_first_year_cost_eur,
            "total_first_year_cost_azn": it_res.net_first_year_cost_azn,
            "is_within_budget": budget >= Decimal(str(it_res.net_first_year_cost_azn)),
            "budget_delta_azn": float(budget - Decimal(str(it_res.net_first_year_cost_azn))),
            "key_regulatory_condition": "ISEE Parificato certification below €25k unlocks full fee waiver and stipend.",
        },
    ]

    dest_list.sort(key=lambda x: x["total_first_year_cost_azn"])
    most_affordable = dest_list[0]["country"]
    highest_cost = dest_list[-1]["country"]

    summary = (
        f"With an annual budget of {float(budget):,.2f} AZN, {most_affordable} provides the most accessible financial route. "
        f"By contrast, {highest_cost} requires the highest initial cash demonstration."
    )

    return DestinationComparisonResult(
        student_budget_azn=float(budget),
        destinations=dest_list,
        most_affordable_country=most_affordable,
        highest_liquidity_country=highest_cost,
        summary_verdict=summary,
    )
