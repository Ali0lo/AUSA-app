"""Pytest test suite for Application Tracker, Document Checklist & University Comparison Workbench."""

import pytest
from starlette.testclient import TestClient

from app.domain.application_tracker import (
    CURATED_COMPARISON_DB,
    AdmissionTier,
    ComparisonRequest,
    DocumentCategory,
    DocumentChecklistRequest,
    TierClassificationRequest,
    classify_application_tier,
    compare_universities,
    generate_document_checklist,
)
from app.main import app

client = TestClient(app)


# ==============================================================================
# Domain Unit Tests
# ==============================================================================

def test_document_checklist_base_academic():
    """Verifies that common academic requirements are present for all destinations."""
    res = generate_document_checklist(DocumentChecklistRequest(country_code="DE", is_state_programme=False))
    doc_ids = {d.id for d in res.documents}
    assert "doc_diploma_transcript" in doc_ids
    assert "doc_recommendation_letters" in doc_ids
    assert "doc_sop" in doc_ids
    assert "doc_cv" in doc_ids
    assert "doc_language_cert" in doc_ids
    assert "doc_passport" in doc_ids
    assert res.total_documents >= 6
    assert res.mandatory_count >= 5


def test_document_checklist_germany_sperrkonto_and_vpd():
    """Verifies that Germany includes VPD and Sperrkonto blocked account."""
    res = generate_document_checklist(DocumentChecklistRequest(country_code="DE", degree_level="master"))
    doc_ids = {d.id for d in res.documents}
    assert "doc_de_vpd" in doc_ids
    assert "doc_de_sperrkonto" in doc_ids
    assert "doc_de_health_insurance" in doc_ids
    assert any("Sperrkonto" in n for n in res.country_specific_notes)


def test_document_checklist_uk_maintenance_and_cas():
    """Verifies that UK includes CAS, 28-day maintenance funds, and TB test."""
    res = generate_document_checklist(DocumentChecklistRequest(country_code="GB", degree_level="master"))
    doc_ids = {d.id for d in res.documents}
    assert "doc_gb_cas" in doc_ids
    assert "doc_gb_maintenance_funds" in doc_ids
    assert "doc_gb_tb_test" in doc_ids
    assert any("28 günlük" in n for n in res.country_specific_notes)


def test_document_checklist_italy_dov_and_isee():
    """Verifies Italy specific DOV/CIMEA, ISEE Parificato, and Universitaly summary."""
    res = generate_document_checklist(DocumentChecklistRequest(country_code="IT"))
    doc_ids = {d.id for d in res.documents}
    assert "doc_it_universitaly" in doc_ids
    assert "doc_it_dov_cimea" in doc_ids
    assert "doc_it_isee_parificato" in doc_ids
    assert any("ISEE Parificato" in n for n in res.country_specific_notes)


def test_document_checklist_state_programme_additions():
    """Verifies that State Programme toggle appends repatriation, medical, and military docs."""
    without_sp = generate_document_checklist(DocumentChecklistRequest(country_code="DE", is_state_programme=False))
    with_sp = generate_document_checklist(DocumentChecklistRequest(country_code="DE", is_state_programme=True))

    assert with_sp.total_documents == without_sp.total_documents + 5
    sp_ids = {d.id for d in with_sp.documents}
    assert "doc_sp_acceptance" in sp_ids
    assert "doc_sp_motivation" in sp_ids
    assert "doc_sp_medical" in sp_ids
    assert "doc_sp_criminal_record" in sp_ids
    assert "doc_sp_military" in sp_ids


def test_classify_application_tier_dream():
    """Verifies that QS Top 50 or highly selective institutions classify as DREAM."""
    req = TierClassificationRequest(
        university_name="University of Oxford",
        country_code="GB",
        qs_rank=3,
        student_gpa=3.8,
        student_gpa_max=4.0,
        student_ielts=7.5,
    )
    result = classify_application_tier(req)
    assert result.tier == AdmissionTier.DREAM
    assert "Dream" in result.badge_label
    assert len(result.action_recommendations) >= 1


def test_classify_application_tier_safety():
    """Verifies that candidates exceeding thresholds classify as SAFETY."""
    req = TierClassificationRequest(
        university_name="Istanbul Technical University",
        country_code="TR",
        qs_rank=404,
        student_gpa=3.85,
        student_gpa_max=4.0,
        student_ielts=7.0,
    )
    result = classify_application_tier(req)
    assert result.tier == AdmissionTier.SAFETY
    assert "Safety" in result.badge_label


def test_classify_application_tier_target():
    """Verifies that standard matching profiles classify as TARGET."""
    req = TierClassificationRequest(
        university_name="Politecnico di Milano",
        country_code="IT",
        qs_rank=111,
        student_gpa=3.3,
        student_gpa_max=4.0,
        student_ielts=6.5,
    )
    result = classify_application_tier(req)
    assert result.tier == AdmissionTier.TARGET
    assert "Target" in result.badge_label


def test_compare_universities_cost_and_pswr_ranking():
    """Tests multi-university side-by-side comparison metrics."""
    req = ComparisonRequest(
        university_ids=["tum_cs", "oxford_cs", "itu_engineering", "cmu_software"],
        student_gpa=3.7,
        student_ielts=7.0,
    )
    res = compare_universities(req)
    assert len(res.items) == 4
    # İTÜ has lowest tuition + living cost
    assert "Istanbul Technical University" in res.lowest_cost_university
    # CMU has 36-month STEM OPT
    assert "Carnegie Mellon" in res.longest_pswr_university
    assert "36 ay" in res.longest_pswr_university
    assert res.best_ranked_university == "University of Oxford"
    assert res.average_first_year_cost_eur > 10000


def test_compare_universities_fallback_when_empty():
    """Tests fallback to top benchmark universities when invalid IDs are passed."""
    res = compare_universities(ComparisonRequest(university_ids=["invalid_unknown_id"]))
    assert len(res.items) == 3
    names = [x.university_name for x in res.items]
    assert "Technical University of Munich (TUM)" in names


def test_curated_database_consistency():
    """Verifies that all curated entries have complete and consistent attributes."""
    assert len(CURATED_COMPARISON_DB) >= 8
    for key, val in CURATED_COMPARISON_DB.items():
        assert val["id"] == key
        assert val["tuition_eur_annual"] >= 0
        assert val["living_cost_eur_monthly"] > 0
        assert val["post_study_work_visa_duration_months"] >= 0
        assert len(val["post_study_work_visa_name"]) >= 5


# ==============================================================================
# FastAPI REST Endpoint Tests
# ==============================================================================

def test_api_get_tiers_endpoint():
    """Tests GET /api/v1/applications/tiers."""
    res = client.get("/api/v1/applications/tiers")
    assert res.status_code == 200
    data = res.json()
    assert "DREAM" in data
    assert "TARGET" in data
    assert "SAFETY" in data
    assert "strategy" in data["DREAM"]


def test_api_get_curated_options_endpoint():
    """Tests GET /api/v1/applications/curated-options."""
    res = client.get("/api/v1/applications/curated-options")
    assert res.status_code == 200
    options = res.json()
    assert len(options) >= 8
    u_names = {x["university_name"] for x in options}
    assert "Technical University of Munich (TUM)" in u_names
    assert "University of Oxford" in u_names


def test_api_post_checklist_endpoint():
    """Tests POST /api/v1/applications/checklist."""
    payload = {
        "country_code": "DE",
        "degree_level": "master",
        "is_state_programme": True,
        "has_scholarship": False,
    }
    res = client.post("/api/v1/applications/checklist", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["country_code"] == "DE"
    assert data["total_documents"] >= 10
    doc_titles = [d["title"] for d in data["documents"]]
    assert any("VPD" in t for t in doc_titles)
    assert any("Sperrkonto" in t for t in doc_titles)


def test_api_post_classify_tier_endpoint():
    """Tests POST /api/v1/applications/classify-tier."""
    payload = {
        "university_name": "Imperial College London",
        "country_code": "GB",
        "qs_rank": 6,
        "program_field": "stem",
        "student_gpa": 3.75,
        "student_gpa_max": 4.0,
        "student_ielts": 7.5,
    }
    res = client.post("/api/v1/applications/classify-tier", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tier"] == "DREAM"
    assert "Dream" in data["badge_label"]


def test_api_post_compare_endpoint():
    """Tests POST /api/v1/applications/compare."""
    payload = {
        "university_ids": ["tum_cs", "rwth_engineering", "polimi_cs"],
        "student_gpa": 3.6,
        "student_ielts": 7.0,
    }
    res = client.post("/api/v1/applications/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3
    assert "lowest_cost_university" in data
    assert "longest_pswr_university" in data
    assert len(data["comparison_summary_notes"]) >= 2


# ==============================================================================
# Extended Integration & Edge-Case Tests
# ==============================================================================

def test_compare_universities_non_existent_id_fallback():
    """Verifies that nonexistent university IDs trigger fallback gracefully to curated items."""
    res = compare_universities(ComparisonRequest(university_ids=["unknown_fake_id_123"]))
    assert len(res.items) >= 3
    u_ids = [item.id for item in res.items]
    assert "tum_cs" in u_ids
    assert "oxford_cs" in u_ids
    assert res.lowest_cost_university is not None


def test_checklist_for_all_target_countries():
    """Verifies checklist generation across all key study destinations."""
    countries = ["DE", "GB", "IT", "TR", "US", "HU"]
    for country in countries:
        res = generate_document_checklist(DocumentChecklistRequest(country_code=country))
        assert res.total_documents >= 5
        assert res.mandatory_count >= 5
        assert len(res.country_name) > 0
        doc_categories = {d.category for d in res.documents}
        assert DocumentCategory.ACADEMIC in doc_categories
        assert DocumentCategory.LEGAL_IMMIGRATION in doc_categories


def test_checklist_mandatory_counts_and_validation():
    """Verifies that mandatory documents and metadata are correctly set for Germany."""
    res = generate_document_checklist(DocumentChecklistRequest(country_code="DE", degree_level="master"))
    assert res.mandatory_count == res.total_documents
    assert all(d.is_mandatory for d in res.documents)
    assert any("Sperrkonto" in d.title for d in res.documents)
    assert any("VPD" in d.title for d in res.documents)


def test_tier_classification_safety_high_gpa():
    """Verifies that high GPA and safe ranking correctly categorizes as SAFETY tier."""
    res = classify_application_tier(
        TierClassificationRequest(
            university_name="Istanbul Technical University",
            country_code="TR",
            qs_rank=404,
            student_gpa=3.85,
            student_gpa_max=4.0,
            student_ielts=7.5,
        )
    )
    assert res.tier == AdmissionTier.SAFETY
    assert "Təminatlı" in res.badge_label


def test_tier_classification_dream_reach():
    """Verifies that top-50 QS universities are classified as DREAM."""
    res = classify_application_tier(
        TierClassificationRequest(
            university_name="Carnegie Mellon University",
            country_code="US",
            qs_rank=28,
            student_gpa=3.5,
            student_gpa_max=4.0,
            student_ielts=7.0,
        )
    )
    assert res.tier == AdmissionTier.DREAM
    assert len(res.risk_factors) >= 1
    assert any("IELTS" in r or "GPA" in r for r in res.risk_factors)


def test_compare_pswr_longest_duration():
    """Verifies that comparing US, UK, and Germany correctly identifies US 36 months STEM OPT."""
    res = compare_universities(ComparisonRequest(university_ids=["cmu_software", "tum_cs", "oxford_cs"]))
    assert len(res.items) == 3
    assert "Carnegie Mellon" in res.longest_pswr_university


def test_api_compare_with_custom_profile_updates_tier():
    """Tests POST /api/v1/applications/compare evaluates tiers dynamically with student GPA."""
    payload = {
        "university_ids": ["oxford_cs", "itu_engineering"],
        "student_gpa": 3.9,
        "student_ielts": 8.0,
    }
    res = client.post("/api/v1/applications/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    tiers = {item["id"]: item["admission_tier"] for item in data["items"]}
    assert tiers["oxford_cs"] == "DREAM"
    assert tiers["itu_engineering"] == "SAFETY"


