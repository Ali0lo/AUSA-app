"""Unit and integration tests for Student Visa Financial Simulator and Blocked Account engine.

Validates:
- Statutory Sperrkonto (§ 16b AufenthG) calculation and provider fees.
- UKVI Appendix Student maintenance rules, 28-day bank holding, and London caps.
- US Form I-20 Cost of Attendance (COA) and consular affidavit safety cushions.
- Italian ISEE-U (ISEE Parificato) formula, equivalence scale, and DSU stipend tiers.
- Multi-currency conversions using official Central Bank of Azerbaijan (CBAR) reference rates.
- FastAPI endpoints under /api/v1/finance/*.
"""

import pytest
from decimal import Decimal
from httpx import ASGITransport, AsyncClient

from app.main import app
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
    GERMANY_STATUTORY_MONTHLY_EUR,
    UKVI_LONDON_MONTHLY_GBP,
    UKVI_OUTSIDE_LONDON_MONTHLY_GBP,
    UKVI_MAX_MAINTENANCE_MONTHS,
    ISEE_MAX_DSU_THRESHOLD_EUR,
    ISEE_TOP_BRACKET_THRESHOLD_EUR,
)


# ==============================================================================
# 1. CURRENCY CONVERSION & FX PRECISION TESTS
# ==============================================================================

def test_exchange_rate_identity():
    """Converting any currency to itself must yield an exact rate of 1.0."""
    for curr in Currency:
        rate = get_exchange_rate(curr, curr)
        assert rate == Decimal("1.0")


def test_cbar_fixed_rates_against_azn():
    """Validates baseline CBAR peg rates against Azerbaijani Manat."""
    assert EXCHANGE_RATES_TO_AZN[Currency.USD] == Decimal("1.7000")
    assert EXCHANGE_RATES_TO_AZN[Currency.EUR] == Decimal("1.8540")
    assert EXCHANGE_RATES_TO_AZN[Currency.GBP] == Decimal("2.2180")
    assert EXCHANGE_RATES_TO_AZN[Currency.TRY] == Decimal("0.0495")


def test_currency_conversion_values():
    """100 USD at 1.70 AZN rate should be exactly 170.00 AZN."""
    azn = convert_amount(100, Currency.USD, Currency.AZN)
    assert azn == Decimal("170.00")

    eur_to_azn = convert_amount(1000, Currency.EUR, Currency.AZN)
    assert eur_to_azn == Decimal("1854.00")


def test_currency_conversion_with_safety_buffer():
    """Applying a 5% safety buffer should multiply the result by 1.05."""
    base = convert_amount(1000, Currency.USD, Currency.AZN, safety_buffer_pct=0.0)
    buffered = convert_amount(1000, Currency.USD, Currency.AZN, safety_buffer_pct=5.0)
    assert base == Decimal("1700.00")
    assert buffered == Decimal("1785.00")


def test_convert_to_all_major():
    """Tests conversion breakdown across AZN, EUR, USD, GBP."""
    res = convert_to_all_major(1000, Currency.EUR)
    assert "AZN" in res
    assert "EUR" in res
    assert "USD" in res
    assert "GBP" in res
    assert res["EUR"] == 1000.0
    assert res["AZN"] == 1854.0


# ==============================================================================
# 2. GERMANY SPERRKONTO DOMAIN TESTS
# ==============================================================================

def test_germany_standard_12_months():
    """Validates 12-month standard Sperrkonto under § 16b AufenthG (€992 * 12 = €11,904)."""
    res = calculate_germany_funds(months=12, city_tier=GermanCityTier.TIER_2_MODERATE, tuition_fee_eur=0.0)

    assert res.statutory_monthly_amount == 992.00
    assert res.number_of_months == 12
    assert res.blocked_account_total == 11904.00
    assert res.account_setup_fee == 89.00
    assert res.account_buffer_deposit == 100.00
    assert res.total_blocked_deposit_required == 12093.00  # 11904 + 89 + 100
    assert res.health_insurance_annual == 1542.00          # 128.50 * 12
    assert res.semester_contributions_annual == 620.00     # 310 * 2 semesters
    assert res.visa_fee == 75.00
    assert res.estimated_arrival_buffer == 1200.00
    assert res.total_first_year_liquidity_eur > 15000.00
    assert res.total_first_year_liquidity_azn > 25000.00
    assert "Sperrkonto" in res.statutory_note


def test_germany_tier_1_expensive_shortfall():
    """Munich or Frankfurt (Tier 1) has higher living costs (+18%), generating a statutory shortfall."""
    res = calculate_germany_funds(months=12, city_tier=GermanCityTier.TIER_1_EXPENSIVE)
    assert res.estimated_monthly_realistic_cost > res.statutory_monthly_amount
    assert res.monthly_statutory_shortfall > 0.0
    assert "actual monthly expenses average" in res.statutory_note


def test_germany_with_private_tuition():
    """Adding Baden-Württemberg or private university tuition (€3,000) increments total."""
    res_free = calculate_germany_funds(tuition_fee_eur=0.0)
    res_tuition = calculate_germany_funds(tuition_fee_eur=3000.0)
    assert res_tuition.total_first_year_liquidity_eur == res_free.total_first_year_liquidity_eur + 3000.0


# ==============================================================================
# 3. UK CAS MAINTENANCE & 28-DAY HOLDING TESTS
# ==============================================================================

def test_uk_outside_london_maintenance():
    """Outside London monthly rate is £1,023 capped at 9 months (£9,207)."""
    res = calculate_uk_funds(
        location_type=UKLocationType.OUTSIDE_LONDON,
        course_tuition_annual_gbp=20000.0,
        deposit_paid_to_cas_gbp=3000.0,
        course_duration_months=12,
    )
    assert res.maintenance_monthly_rate_gbp == 1023.00
    assert res.maintenance_months_assessed == 9
    assert res.maintenance_total_gbp == 9207.00
    assert res.course_tuition_annual_gbp == 20000.00
    assert res.deposit_paid_to_cas_gbp == 3000.00
    assert res.outstanding_tuition_gbp == 17000.00
    assert res.total_funds_to_hold_28_days_gbp > 26000.00
    assert "28 consecutive days" in res.holding_rule_statement


def test_uk_inner_london_maintenance():
    """Inner London monthly rate is £1,334 capped at 9 months (£12,006)."""
    res = calculate_uk_funds(
        location_type=UKLocationType.INNER_LONDON,
        course_tuition_annual_gbp=22000.0,
        deposit_paid_to_cas_gbp=2000.0,
        course_duration_months=9,
    )
    assert res.maintenance_monthly_rate_gbp == 1334.00
    assert res.maintenance_total_gbp == 12006.00
    assert res.outstanding_tuition_gbp == 20000.00


def test_uk_full_tuition_deposit():
    """When full tuition is already paid to CAS, outstanding tuition is zero."""
    res = calculate_uk_funds(
        location_type=UKLocationType.OUTSIDE_LONDON,
        course_tuition_annual_gbp=15000.0,
        deposit_paid_to_cas_gbp=15000.0,
    )
    assert res.outstanding_tuition_gbp == 0.0
    assert res.breakdown["outstanding_tuition_gbp"] == 0.0


# ==============================================================================
# 4. US I-20 COST OF ATTENDANCE & AFFIDAVIT TESTS
# ==============================================================================

def test_us_i20_coa_calculation():
    """Validates US I-20 net calculation with institutional scholarship deduction."""
    res = calculate_us_funds(
        tuition_annual_usd=30000.0,
        institutional_fees_usd=2000.0,
        location_tier=USLivingLocationTier.SUBURBAN_MODERATE,
        scholarship_award_usd=10000.0,
    )
    # Living room & board suburban = 16,500; health = 2,400; books = 1,200; personal = 2,200. Total non-tuition = 22,300.
    # Gross = 30000 + 2000 + 22300 = 54,300. Net = 54,300 - 10,000 = 44,300.
    assert res.official_i20_total_usd == 44300.00
    assert res.sevis_fee_usd == 350.00
    assert res.mrv_visa_fee_usd == 185.00
    assert res.recommended_consular_buffer_usd == 44300.00 * 0.15
    assert res.total_recommended_affidavit_usd == 44300.00 + 350.00 + 185.00 + (44300.00 * 0.15)
    assert "Form I-20" in res.consular_advice


def test_us_high_metropolitan_tier():
    """Metropolitan high tier (NYC/SF/Boston) should increase room and board to $22,500."""
    res_metro = calculate_us_funds(location_tier=USLivingLocationTier.METROPOLITAN_HIGH)
    res_suburban = calculate_us_funds(location_tier=USLivingLocationTier.SUBURBAN_MODERATE)
    assert res_metro.living_room_and_board_usd == 22500.00
    assert res_metro.official_i20_total_usd > res_suburban.official_i20_total_usd


# ==============================================================================
# 5. ITALY ISEE-U & DSU SCHOLARSHIP TESTS
# ==============================================================================

def test_italy_dsu_qualification_low_income():
    """Modest household income (e.g. 15,000 AZN / 4 people) qualifies for DSU fee waiver and stipend."""
    res = calculate_italy_funds(
        family_members_count=4,
        family_annual_income_azn=15000.0,
        real_estate_abroad_azn=50000.0,
        city_tier=ItalyCityTier.TIER_2_MAJOR_STUDENT,
        base_tuition_eur=3000.0,
    )
    assert res.calculated_isee_parificato_eur < float(ISEE_TOP_BRACKET_THRESHOLD_EUR)
    assert res.qualifies_for_dsu_fee_waiver is True
    assert res.qualifies_for_dsu_cash_stipend is True
    assert res.estimated_dsu_cash_stipend_eur == 7200.00
    assert res.annual_tuition_after_dsu_eur == 156.00  # Regional administrative stamp duty only
    assert "BELOW" in res.dsu_eligibility_verdict


def test_italy_high_income_no_dsu():
    """High income and substantial real estate exceeds €25,000 ISEE threshold."""
    res = calculate_italy_funds(
        family_members_count=2,
        family_annual_income_azn=80000.0,
        real_estate_abroad_azn=300000.0,
        base_tuition_eur=4000.0,
    )
    assert res.calculated_isee_parificato_eur > float(ISEE_MAX_DSU_THRESHOLD_EUR)
    assert res.qualifies_for_dsu_fee_waiver is False
    assert res.estimated_dsu_cash_stipend_eur == 0.0
    assert res.annual_tuition_after_dsu_eur == 4000.00
    assert "exceeds" in res.dsu_eligibility_verdict


# ==============================================================================
# 6. MULTI-DESTINATION COMPARATIVE BENCHMARK TESTS
# ==============================================================================

def test_destination_comparison_engine():
    """Benchmarks all 4 destinations against a 30,000 AZN student budget."""
    res = compare_study_destinations_finance(student_annual_budget_azn=30000.0)
    assert len(res.destinations) == 4
    countries = [d["country"] for d in res.destinations]
    assert "Germany" in countries
    assert "United Kingdom" in countries
    assert "United States" in countries
    assert "Italy" in countries
    # Results must be sorted ascending by AZN cost
    costs = [d["total_first_year_cost_azn"] for d in res.destinations]
    assert costs == sorted(costs)
    assert res.student_budget_azn == 30000.0
    assert len(res.summary_verdict) > 20


# ==============================================================================
# 7. FASTAPI API INTEGRATION TESTS (/api/v1/finance/*)
# ==============================================================================

@pytest.mark.asyncio
async def test_api_exchange_rates():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/finance/rates")
        assert res.status_code == 200
        data = res.json()
        assert data["base_currency"] == "AZN"
        assert "EUR" in data["rates_to_azn"]
        assert "USD" in data["rates_to_azn"]
        assert "cross_rates" in data
        assert data["cross_rates"]["EUR"]["AZN"] == 1.8540


@pytest.mark.asyncio
async def test_api_currency_convert():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "amount": 1000.0,
            "from_currency": "EUR",
            "to_currency": "AZN",
            "safety_buffer_pct": 2.5,
        }
        res = await client.post("/api/v1/finance/convert", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["amount"] == 1000.0
        assert data["from_currency"] == "EUR"
        assert data["to_currency"] == "AZN"
        assert data["converted_amount"] > 1854.00
        assert "converted_all_major" in data


@pytest.mark.asyncio
async def test_api_germany_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "months": 12,
            "city_tier": "tier_2_moderate",
            "tuition_fee_eur": 0.0,
            "include_arrival_buffer": True,
            "exchange_safety_buffer_pct": 3.0,
        }
        res = await client.post("/api/v1/finance/germany", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "Germany"
        assert data["blocked_account_total"] == 11904.0
        assert data["total_blocked_deposit_required"] == 12093.0
        assert data["total_first_year_liquidity_azn"] > 25000.0


@pytest.mark.asyncio
async def test_api_uk_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "location_type": "inner_london",
            "course_tuition_annual_gbp": 20000.0,
            "deposit_paid_to_cas_gbp": 4000.0,
            "course_duration_months": 12,
            "exchange_safety_buffer_pct": 3.0,
        }
        res = await client.post("/api/v1/finance/uk", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "United Kingdom"
        assert data["maintenance_months_assessed"] == 9
        assert data["maintenance_monthly_rate_gbp"] == 1334.0
        assert data["outstanding_tuition_gbp"] == 16000.0
        assert "28 consecutive days" in data["holding_rule_statement"]


@pytest.mark.asyncio
async def test_api_usa_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "tuition_annual_usd": 32000.0,
            "institutional_fees_usd": 2200.0,
            "location_tier": "metropolitan_high",
            "scholarship_award_usd": 12000.0,
            "exchange_safety_buffer_pct": 3.0,
        }
        res = await client.post("/api/v1/finance/usa", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "United States"
        assert data["official_i20_total_usd"] > 30000.0
        assert data["sevis_fee_usd"] == 350.0
        assert data["mrv_visa_fee_usd"] == 185.0


@pytest.mark.asyncio
async def test_api_italy_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "family_members_count": 4,
            "family_annual_income_azn": 18000.0,
            "real_estate_abroad_azn": 60000.0,
            "city_tier": "tier_2_major_student",
            "base_tuition_eur": 3000.0,
            "exchange_safety_buffer_pct": 3.0,
        }
        res = await client.post("/api/v1/finance/italy", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "Italy"
        assert data["qualifies_for_dsu_fee_waiver"] is True
        assert data["annual_tuition_after_dsu_eur"] == 156.0


@pytest.mark.asyncio
async def test_api_compare_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "student_annual_budget_azn": 40000.0,
            "tuition_eur": 0.0,
            "tuition_gbp": 16000.0,
            "tuition_usd": 26000.0,
            "tuition_italy_eur": 3200.0,
            "family_members_count": 4,
            "family_income_azn": 20000.0,
        }
        res = await client.post("/api/v1/finance/compare", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["student_budget_azn"] == 40000.0
        assert len(data["destinations"]) == 4
        assert "most_affordable_country" in data
        assert "summary_verdict" in data

