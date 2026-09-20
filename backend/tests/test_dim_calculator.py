"""Comprehensive unit and integration tests for the DİM 700-point score simulator and historical specialty recommendation engine.
"""

from fastapi.testclient import TestClient
import pytest

from app.domain.dim_calculator import (
    BlokInput,
    BuraxilisInput,
    ChanceLevel,
    DimCalculationRequest,
    DimGroup,
    SubGroup,
    SubjectQuestionInput,
    calculate_subject_score,
    calculate_total_dim_score,
    get_all_dim_group_metadata,
    get_default_blok_input,
    get_specialty_recommendations,
    load_cutoff_history_records,
)
from app.main import app

client = TestClient(app)


class TestDimDomainLogic:
    """Unit tests for DİM scoring rules and formulas."""

    def test_dim_group_metadata(self):
        meta = get_all_dim_group_metadata()
        assert len(meta) == 5
        groups = [m["group"] for m in meta]
        assert "I qrup" in groups
        assert "II qrup" in groups
        assert "III qrup" in groups
        assert "IV qrup" in groups
        assert "V qrup" in groups

        # Group 1 subgroups
        g1 = next(m for m in meta if m["group"] == "I qrup")
        sg_codes = [sg["code"] for sg in g1["subgroups"]]
        assert "RI" in sg_codes
        assert "RK" in sg_codes
        assert g1["max_total"] == 700

    def test_buraxilis_penalty_and_scaling(self):
        # 20 closed questions, 4 wrong => net closed = 16 - (4 * 0.25) = 15.0
        # 20 open points max, scored 10.0 => total raw = 15.0 + 10.0 = 25.0
        # max raw = 20 + 20 = 40.0 => scaled = (25.0 / 40.0) * 100 = 62.5
        subj = SubjectQuestionInput(
            subject_key="native_language",
            subject_name="Azərbaycan dili",
            closed_correct=16,
            closed_incorrect=4,
            open_points=10.0,
            max_closed=20,
            max_open_points=20.0,
            max_scaled_points=100.0,
        )
        res = calculate_subject_score(subj)
        assert res.net_closed == 15.0
        assert res.open_points == 10.0
        assert res.total_raw == 25.0
        assert res.scaled_score == 62.5
        assert res.percentage == 62.5

    def test_buraxilis_open_questions_no_penalty(self):
        # Mathematics: 13 closed (all correct = 13), 0 incorrect => net closed = 13.0
        # open points: 19.0 max, scored 19.0 => total raw = 32.0 / 32.0 => 100.0
        subj = SubjectQuestionInput(
            subject_key="mathematics",
            subject_name="Riyaziyyat",
            closed_correct=13,
            closed_incorrect=0,
            open_points=19.0,
            max_closed=13,
            max_open_points=19.0,
            max_scaled_points=100.0,
        )
        res = calculate_subject_score(subj)
        assert res.scaled_score == 100.0
        assert res.percentage == 100.0

    def test_buraxilis_direct_score_override(self):
        subj = SubjectQuestionInput(
            subject_key="foreign_language",
            subject_name="İngilis dili",
            direct_score=85.0,
            max_scaled_points=100.0,
        )
        res = calculate_subject_score(subj)
        assert res.scaled_score == 85.0

    def test_blok_group1_ri_subgroup(self):
        blok = get_default_blok_input(DimGroup.GROUP_1, SubGroup.RI)
        assert blok.subject_1.subject_name == "Riyaziyyat"
        assert blok.subject_1.max_scaled_points == 150.0
        assert blok.subject_2.subject_name == "Fizika"
        assert blok.subject_2.max_scaled_points == 150.0
        assert blok.subject_3.subject_name == "İnformatika"
        assert blok.subject_3.max_scaled_points == 100.0
        assert (
            blok.subject_1.max_scaled_points + blok.subject_2.max_scaled_points + blok.subject_3.max_scaled_points
            == 400.0
        )

    def test_blok_group1_rk_subgroup(self):
        blok = get_default_blok_input(DimGroup.GROUP_1, SubGroup.RK)
        assert blok.subject_3.subject_name == "Kimya"
        assert blok.subject_3.max_scaled_points == 100.0

    def test_blok_group2(self):
        blok = get_default_blok_input(DimGroup.GROUP_2)
        assert blok.subject_1.subject_name == "Riyaziyyat"
        assert blok.subject_2.subject_name == "Coğrafiya"
        assert blok.subject_3.subject_name == "Tarix"
        assert (
            blok.subject_1.max_scaled_points + blok.subject_2.max_scaled_points + blok.subject_3.max_scaled_points
            == 400.0
        )

    def test_blok_group3_subgroups(self):
        blok_dt = get_default_blok_input(DimGroup.GROUP_3, SubGroup.DT)
        assert blok_dt.subject_1.subject_name == "Azərbaycan dili"
        assert blok_dt.subject_2.subject_name == "Tarix"
        assert blok_dt.subject_3.subject_name == "Ədəbiyyat"

        blok_tc = get_default_blok_input(DimGroup.GROUP_3, SubGroup.TC)
        assert blok_tc.subject_3.subject_name == "Coğrafiya"

    def test_blok_group4(self):
        blok = get_default_blok_input(DimGroup.GROUP_4)
        assert blok.subject_1.subject_name == "Biologiya"
        assert blok.subject_2.subject_name == "Kimya"
        assert blok.subject_3.subject_name == "Fizika"

    def test_total_dim_score_limits(self):
        # Maximum possible score
        req_max = DimCalculationRequest(
            group=DimGroup.GROUP_1,
            subgroup=SubGroup.RI,
            buraxilis=BuraxilisInput(direct_total_score=300.0),
            blok=BlokInput(direct_total_score=400.0),
        )
        res_max = calculate_total_dim_score(req_max)
        assert res_max.buraxilis_score == 300.0
        assert res_max.blok_score == 400.0
        assert res_max.total_score == 700.0
        assert res_max.percentage == 100.0
        assert res_max.clears_bhos_benchmark is True
        assert res_max.passed_competition_minimum is True

        # Zero score
        req_min = DimCalculationRequest(
            group=DimGroup.GROUP_1,
            subgroup=SubGroup.RI,
            buraxilis=BuraxilisInput(direct_total_score=0.0),
            blok=BlokInput(direct_total_score=0.0),
        )
        res_min = calculate_total_dim_score(req_min)
        assert res_min.total_score == 0.0
        assert res_min.percentage == 0.0
        assert res_min.clears_bhos_benchmark is False
        assert res_min.passed_competition_minimum is False

    def test_bhos_650_benchmark_clearance(self):
        req_649 = DimCalculationRequest(
            group=DimGroup.GROUP_1,
            subgroup=SubGroup.RI,
            buraxilis=BuraxilisInput(direct_total_score=280.0),
            blok=BlokInput(direct_total_score=369.0),
        )
        res_649 = calculate_total_dim_score(req_649)
        assert res_649.total_score == 649.0
        assert res_649.clears_bhos_benchmark is False

        req_650 = DimCalculationRequest(
            group=DimGroup.GROUP_1,
            subgroup=SubGroup.RI,
            buraxilis=BuraxilisInput(direct_total_score=280.0),
            blok=BlokInput(direct_total_score=370.0),
        )
        res_650 = calculate_total_dim_score(req_650)
        assert res_650.total_score == 650.0
        assert res_650.clears_bhos_benchmark is True


class TestSpecialtyRecommendations:
    """Tests for the historical cutoff matching and chance tier categorization."""

    def test_load_cutoff_records(self):
        records = load_cutoff_history_records()
        assert len(records) > 2000
        first = records[0]
        assert "program_code" in first
        assert "university_name" in first
        assert "intake_year" in first
        assert "cutoff_value" in first

    def test_chance_tier_categorization(self):
        # Create a mock candidate with 600.0 points
        breakdown = calculate_total_dim_score(
            DimCalculationRequest(
                group=DimGroup.GROUP_1,
                subgroup=SubGroup.RI,
                buraxilis=BuraxilisInput(direct_total_score=260.0),
                blok=BlokInput(direct_total_score=340.0),
            )
        )
        assert breakdown.total_score == 600.0

        mock_records = [
            {
                "program_code": "safe-prog",
                "university_name": "AzTU",
                "department_name": "Proqram mühəndisliyi",
                "score_type": "I qrup",
                "scholarship_type": "dövlət sifarişli",
                "intake_year": 2025,
                "cutoff_value": 550.0,  # delta = +50.0 -> SAFE
            },
            {
                "program_code": "real-prog",
                "university_name": "BDU",
                "department_name": "Kompüter elmləri",
                "score_type": "I qrup",
                "scholarship_type": "dövlət sifarişli",
                "intake_year": 2025,
                "cutoff_value": 590.0,  # delta = +10.0 -> REALISTIC
            },
            {
                "program_code": "target-prog",
                "university_name": "BMU",
                "department_name": "İnformasiya təhlükəsizliyi",
                "score_type": "I qrup",
                "scholarship_type": "dövlət sifarişli",
                "intake_year": 2025,
                "cutoff_value": 615.0,  # delta = -15.0 -> TARGET
            },
            {
                "program_code": "asp-prog",
                "university_name": "ADA",
                "department_name": "Kompüter elmləri",
                "score_type": "I qrup",
                "scholarship_type": "dövlət sifarişli",
                "intake_year": 2025,
                "cutoff_value": 680.0,  # delta = -80.0 -> ASPIRATIONAL
            },
        ]

        resp = get_specialty_recommendations(breakdown, records=mock_records)
        assert resp.total_matched == 4
        assert resp.safe_count == 1
        assert resp.realistic_count == 1
        assert resp.target_count == 1
        assert resp.aspirational_count == 1

        recs = resp.recommendations
        assert recs[0].program_code == "safe-prog"
        assert recs[0].chance_level == ChanceLevel.SAFE
        assert recs[1].program_code == "real-prog"
        assert recs[1].chance_level == ChanceLevel.REALISTIC
        assert recs[2].program_code == "target-prog"
        assert recs[2].chance_level == ChanceLevel.TARGET
        assert recs[3].program_code == "asp-prog"
        assert recs[3].chance_level == ChanceLevel.ASPIRATIONAL

    def test_bhos_650_rule_in_recommendations(self):
        breakdown = calculate_total_dim_score(
            DimCalculationRequest(
                group=DimGroup.GROUP_1,
                buraxilis=BuraxilisInput(direct_total_score=280.0),
                blok=BlokInput(direct_total_score=380.0),
            )
        )
        mock_bhos = [
            {
                "program_code": "bhos-cyber",
                "university_name": "Baku Higher Oil School (BANM / BHOS)",
                "department_name": "İnformasiya təhlükəsizliyi",
                "score_type": "I qrup",
                "scholarship_type": "dövlət sifarişli",
                "intake_year": 2024,
                "cutoff_value": 687.1,  # No 2025 cutoff provided
            }
        ]
        resp = get_specialty_recommendations(breakdown, records=mock_bhos)
        assert resp.total_matched == 1
        rec = resp.recommendations[0]
        assert rec.is_bhos is True
        assert rec.cutoff_2024 == 687.1

    def test_filter_by_university_and_search(self):
        breakdown = calculate_total_dim_score(
            DimCalculationRequest(
                group=DimGroup.GROUP_1,
                buraxilis=BuraxilisInput(direct_total_score=260.0),
                blok=BlokInput(direct_total_score=350.0),
            )
        )
        resp = get_specialty_recommendations(
            breakdown,
            university_filter="ADA",
            search_query="Kompüter",
        )
        for r in resp.recommendations:
            assert "ADA" in r.university_name
            assert "Kompüter" in r.department_name or "kompüter" in r.department_name.lower()


class TestDimApiEndpoints:
    """Integration tests for FastAPI /api/v1/dim endpoints."""

    def test_api_groups(self):
        resp = client.get("/api/v1/dim/groups")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5
        assert data[0]["group"] == "I qrup"

    def test_api_default_inputs(self):
        resp = client.get("/api/v1/dim/default-inputs?group=I%20qrup&subgroup=RI")
        assert resp.status_code == 200
        data = resp.json()
        assert data["group"] == "I qrup"
        assert data["subgroup"] == "RI"
        assert "buraxilis" in data
        assert "blok" in data

    def test_api_calculate(self):
        payload = {
            "group": "I qrup",
            "subgroup": "RI",
            "buraxilis": {
                "native_language": {"subject_key": "az", "subject_name": "Az", "direct_score": 90.0},
                "mathematics": {"subject_key": "math", "subject_name": "Math", "direct_score": 95.0},
                "foreign_language": {"subject_key": "eng", "subject_name": "Eng", "direct_score": 90.0},
            },
            "blok": {
                "subject_1": {"subject_key": "math", "subject_name": "Math", "direct_score": 145.0},
                "subject_2": {"subject_key": "phys", "subject_name": "Phys", "direct_score": 140.0},
                "subject_3": {"subject_key": "cs", "subject_name": "CS", "direct_score": 95.0},
            },
        }
        resp = client.post("/api/v1/dim/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["buraxilis_score"] == 275.0
        assert data["blok_score"] == 380.0
        assert data["total_score"] == 655.0
        assert data["clears_bhos_benchmark"] is True
        assert data["passed_competition_minimum"] is True

    def test_api_recommend(self):
        payload = {
            "candidate_score": 620.0,
            "group": "I qrup",
            "subgroup": "RI",
            "chance_filter": "SAFE",
            "limit": 10,
        }
        resp = client.post("/api/v1/dim/recommend", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "score_breakdown" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 10
        for r in data["recommendations"]:
            assert r["chance_level"] == "SAFE"
