"""Unit and integration tests for Global Scholarship Engine & Qualification Assessment.

Validates:
- 14 international and bilateral scholarship instruments and statutory criteria.
- Chevening 2,800 work hour gate, work experience accrual, and return obligations.
- Türkiye Bursları age gates (under 21 for bachelor, under 30 for master).
- Italian DSU needs-based ISEE-U ceiling (€25,000 threshold).
- Eiffel Excellence France age limit (under 26 for master).
- SOCAR corporate employment gate.
- Baku Higher Oil School 650+ DİM full scholarship standard.
- FastAPI endpoints under /api/v1/scholarships/*.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.global_scholarships import (
    ALL_GLOBAL_SCHOLARSHIPS,
    CHEVENING_UK,
    FULBRIGHT_USA,
    TURKIYE_BURSLARI,
    STIPENDIUM_HUNGARICUM,
    ITALIAN_DSU_REGIONAL,
    EIFFEL_EXCELLENCE_FRANCE,
    SOCAR_OVERSEAS_AZ,
    BHOS_FULL_SCHOLARSHIP,
    FundingTier,
    FundingType,
    ScholarshipStatus,
    StudentScholarshipProfile,
    evaluate_all_scholarships,
    evaluate_scholarship,
)


# ==============================================================================
# 1. DOMAIN CATALOGUE INTEGRITY TESTS
# ==============================================================================

def test_catalogue_size_and_uniqueness():
    """Validates that exactly 14 comprehensive scholarships exist with unique keys."""
    assert len(ALL_GLOBAL_SCHOLARSHIPS) == 14
    keys = [s.key for s in ALL_GLOBAL_SCHOLARSHIPS]
    assert len(keys) == len(set(keys)), "All scholarship keys must be strictly unique"


def test_catalogue_required_fields():
    """Ensures every scholarship instrument carries required statutory fields."""
    for s in ALL_GLOBAL_SCHOLARSHIPS:
        assert len(s.name) > 3
        assert len(s.provider) > 3
        assert len(s.coverage_summary) > 10
        assert len(s.citation) > 10
        assert s.official_portal_url.startswith("http")
        assert len(s.degree_levels) >= 1
        for lvl in s.degree_levels:
            assert lvl in ("bachelor", "master", "phd")


def test_bachelor_scholarship_availability():
    """Validates which instruments reach bachelor level (findings per research brief)."""
    bachelor_scholarships = [s for s in ALL_GLOBAL_SCHOLARSHIPS if "bachelor" in s.degree_levels]
    keys = {s.key for s in bachelor_scholarships}
    # State Program, Turkiye Burslari, Stipendium Hungaricum, Italian DSU, CSC China, BHOS
    assert "turkiye-burslari" in keys
    assert "stipendium-hungaricum" in keys
    assert "italian-dsu-regional" in keys
    assert "csc-china" in keys
    assert "bhos-state-order" in keys
    assert "dp-azerbaijan" in keys


# ==============================================================================
# 2. DISCRETE GATE EVALUATION TESTS
# ==============================================================================

def test_chevening_work_hours_qualification():
    """Chevening strictly requires 2,800 hours of documented work experience."""
    # 1. Short of hours -> UNLOCKABLE (hours accrue)
    profile_short = StudentScholarshipProfile(
        level_sought="master",
        work_experience_hours=1500,
        ielts=7.0,
        gpa=3.5,
    )
    ev_short = evaluate_scholarship(CHEVENING_UK, profile_short)
    assert ev_short.status == ScholarshipStatus.UNLOCKABLE
    assert any("short of 2,800 required" in msg for msg in ev_short.gates_missing)

    # 2. Clears hours -> OPEN
    profile_clears = StudentScholarshipProfile(
        level_sought="master",
        work_experience_hours=3200,
        ielts=7.0,
        gpa=3.5,
    )
    ev_clears = evaluate_scholarship(CHEVENING_UK, profile_clears)
    assert ev_clears.status == ScholarshipStatus.OPEN
    assert any("clears 2,800 hour requirement" in msg for msg in ev_clears.gates_met)

    # 3. Bachelor applicant -> BLOCKED (Master's only)
    profile_bachelor = StudentScholarshipProfile(
        level_sought="bachelor",
        work_experience_hours=3000,
    )
    ev_bachelor = evaluate_scholarship(CHEVENING_UK, profile_bachelor)
    assert ev_bachelor.status == ScholarshipStatus.BLOCKED
    assert any("Level mismatch" in msg for msg in ev_bachelor.gates_blocked)


def test_turkiye_burslari_age_gates():
    """Türkiye Bursları enforces strict age gates: under 21 for bachelor, under 30 for master."""
    # Bachelor over 21 is blocked
    p_bach_old = StudentScholarshipProfile(level_sought="bachelor", age=22, gpa=3.5)
    ev_bach_old = evaluate_scholarship(TURKIYE_BURSLARI, p_bach_old)
    assert ev_bach_old.status == ScholarshipStatus.BLOCKED
    assert any("exceeds the maximum 21 threshold" in msg for msg in ev_bach_old.gates_blocked)

    # Bachelor under 21 clears age
    p_bach_young = StudentScholarshipProfile(level_sought="bachelor", age=18, gpa=3.5)
    ev_bach_young = evaluate_scholarship(TURKIYE_BURSLARI, p_bach_young)
    assert ev_bach_young.status == ScholarshipStatus.OPEN
    assert any("satisfies under 21 limit" in msg for msg in ev_bach_young.gates_met)

    # Master over 30 is blocked
    p_mast_old = StudentScholarshipProfile(level_sought="master", age=32, gpa=3.5)
    ev_mast_old = evaluate_scholarship(TURKIYE_BURSLARI, p_mast_old)
    assert ev_mast_old.status == ScholarshipStatus.BLOCKED
    assert any("exceeds the maximum 30 threshold" in msg for msg in ev_mast_old.gates_blocked)


def test_eiffel_france_age_limit():
    """Eiffel Excellence strictly caps Master applicants at 25 years old."""
    p_eligible = StudentScholarshipProfile(level_sought="master", age=24, gpa=3.8, ielts=7.0)
    ev_eligible = evaluate_scholarship(EIFFEL_EXCELLENCE_FRANCE, p_eligible)
    assert ev_eligible.status == ScholarshipStatus.OPEN

    p_ineligible = StudentScholarshipProfile(level_sought="master", age=26, gpa=3.8, ielts=7.0)
    ev_ineligible = evaluate_scholarship(EIFFEL_EXCELLENCE_FRANCE, p_ineligible)
    assert ev_ineligible.status == ScholarshipStatus.BLOCKED
    assert any("exceeds the maximum 25 threshold" in msg for msg in ev_ineligible.gates_blocked)


def test_italian_dsu_financial_need():
    """Italian DSU evaluates household income against the €25,000 ISEE threshold."""
    # 20,000 AZN (~€10,787) clears threshold
    p_low_inc = StudentScholarshipProfile(
        level_sought="bachelor",
        family_household_income_azn=20000.0,
    )
    ev_low_inc = evaluate_scholarship(ITALIAN_DSU_REGIONAL, p_low_inc)
    assert ev_low_inc.status == ScholarshipStatus.OPEN
    assert any("within the €25,000 ISEE ceiling" in msg for msg in ev_low_inc.gates_met)

    # 60,000 AZN (~€32,362) exceeds threshold
    p_high_inc = StudentScholarshipProfile(
        level_sought="bachelor",
        family_household_income_azn=60000.0,
    )
    ev_high_inc = evaluate_scholarship(ITALIAN_DSU_REGIONAL, p_high_inc)
    assert ev_high_inc.status == ScholarshipStatus.BLOCKED
    assert any("exceeds the €25,000 ISEE threshold" in msg for msg in ev_high_inc.gates_blocked)


def test_socar_employer_gate():
    """SOCAR overseas scholarship is open exclusively to SOCAR group employees."""
    p_socar = StudentScholarshipProfile(
        level_sought="master",
        age=28,
        employer="SOCAR Upstream LLC",
        gpa=3.5,
        ielts=7.0,
    )
    ev_socar = evaluate_scholarship(SOCAR_OVERSEAS_AZ, p_socar)
    assert ev_socar.status == ScholarshipStatus.OPEN
    assert any("Employment match" in msg for msg in ev_socar.gates_met)

    p_other = StudentScholarshipProfile(level_sought="master", employer="Pasha Bank", gpa=3.5, ielts=7.0)
    ev_other = evaluate_scholarship(SOCAR_OVERSEAS_AZ, p_other)
    assert ev_other.status == ScholarshipStatus.BLOCKED
    assert any("open exclusively to SOCAR group employees" in msg for msg in ev_other.gates_blocked)


def test_bhos_dim_score_gate():
    """BHOS full state scholarship requires 650+ DİM entrance score."""
    p_clears = StudentScholarshipProfile(level_sought="bachelor", dim_score=670.0)
    ev_clears = evaluate_scholarship(BHOS_FULL_SCHOLARSHIP, p_clears)
    assert ev_clears.status == ScholarshipStatus.OPEN
    assert any("clears the 650+ full scholarship standard" in msg for msg in ev_clears.gates_met)

    p_below = StudentScholarshipProfile(level_sought="bachelor", dim_score=630.0)
    ev_below = evaluate_scholarship(BHOS_FULL_SCHOLARSHIP, p_below)
    assert ev_below.status == ScholarshipStatus.BLOCKED
    assert any("below the 650+ benchmark" in msg for msg in ev_below.gates_blocked)


def test_evaluate_all_sorting():
    """evaluate_all_scholarships must sort OPEN first, then UNLOCKABLE, then BLOCKED."""
    profile = StudentScholarshipProfile(
        level_sought="master",
        age=24,
        gpa=3.6,
        ielts=7.0,
        work_experience_hours=3000,
        employer="SOCAR AQS",
    )
    all_res = evaluate_all_scholarships(profile)
    assert len(all_res) == 14
    statuses = [r.status for r in all_res]

    open_indices = [i for i, s in enumerate(statuses) if s == ScholarshipStatus.OPEN]
    unlock_indices = [i for i, s in enumerate(statuses) if s == ScholarshipStatus.UNLOCKABLE]
    block_indices = [i for i, s in enumerate(statuses) if s == ScholarshipStatus.BLOCKED]

    if open_indices and unlock_indices:
        assert max(open_indices) < min(unlock_indices)
    if unlock_indices and block_indices:
        assert max(unlock_indices) < min(block_indices)


# ==============================================================================
# 3. FASTAPI ENDPOINT INTEGRATION TESTS (/api/v1/scholarships/*)
# ==============================================================================

@pytest.mark.asyncio
async def test_api_list_scholarships():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/scholarships")
        assert res.status_code == 200
        data = res.json()
        assert data["total_count"] == 14
        assert len(data["items"]) == 14
        assert len(data["available_countries"]) > 5
        assert "bachelor" in data["available_degree_levels"]


@pytest.mark.asyncio
async def test_api_filter_scholarships_by_country():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # UK filter should return Chevening and GREAT
        res = await client.get("/api/v1/scholarships?country=GB")
        assert res.status_code == 200
        data = res.json()
        assert data["total_count"] == 2
        names = [s["name"] for s in data["items"]]
        assert any("Chevening" in n for n in names)
        assert any("GREAT" in n for n in names)


@pytest.mark.asyncio
async def test_api_filter_scholarships_by_degree():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/scholarships?degree_level=bachelor")
        assert res.status_code == 200
        data = res.json()
        assert data["total_count"] >= 5
        for item in data["items"]:
            assert "bachelor" in item["degree_levels"]


@pytest.mark.asyncio
async def test_api_get_scholarship_detail():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/scholarships/chevening-uk")
        assert res.status_code == 200
        data = res.json()
        assert data["key"] == "chevening-uk"
        assert data["work_experience_hours"] == 2800
        assert len(data["selection_stages"]) > 2
        assert len(data["eligibility_criteria"]) > 2


@pytest.mark.asyncio
async def test_api_get_scholarship_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/scholarships/invalid-scholarship-id")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_api_evaluate_scholarships():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "level_sought": "master",
            "age": 24,
            "gpa": 3.7,
            "gpa_scale": "4.0",
            "ielts": 7.5,
            "work_experience_hours": 3000,
            "employer": "SOCAR Engineering",
            "is_azerbaijani_citizen": True,
            "family_household_income_azn": 18000.0,
        }
        res = await client.post("/api/v1/scholarships/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_evaluated"] == 14
        assert data["open_count"] >= 3
        assert len(data["results"]) == 14
        # Verify Chevening evaluation item
        chev_item = next(r for r in data["results"] if r["scholarship"]["key"] == "chevening-uk")
        assert chev_item["status"] == "open"
        assert any("clears 2,800 hour" in msg for msg in chev_item["gates_met"])
