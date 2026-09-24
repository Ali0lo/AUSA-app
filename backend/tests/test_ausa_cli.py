"""
Pytest Test Suite for AUSA Developer & Admissions CLI (backend/cli/ausa_cli.py).

Tests all CLI commands, argument parsers, formatters, and JSON outputs:
- dim-calc (direct scores and sub-exam question simulations)
- finance (Germany Sperrkonto, UK CAS funds, US COA, Italy ISEE-U, 4-country benchmark)
- scholarships (evaluation of 14 global scholarships)
- timeline (milestones, urgency filtering)
- compare (multi-university side-by-side matrices)
- checklist (country-specific prerequisite document generator)
- sop-check (narrative evaluation, cliché detection, and passive voice auditing)
"""

import json
from io import StringIO
import pytest
from unittest.mock import patch

try:
    from cli.ausa_cli import main, build_parser, CLI_VERSION
except ImportError:
    from backend.cli.ausa_cli import main, build_parser, CLI_VERSION


def run_cli_args(args: list[str]) -> tuple[int, str]:
    """Helper to invoke CLI main with captured stdout."""
    stdout_buf = StringIO()
    with patch("sys.stdout", stdout_buf):
        try:
            code = main(args)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0
    return code, stdout_buf.getvalue()


# ==============================================================================
# 1. Version, Banner & Help Tests
# ==============================================================================

def test_cli_version():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])


def test_cli_no_args_prints_help():
    code, out = run_cli_args([])
    assert code == 0
    assert "AUSA ADMISSIONS & UNIVERSITY ADVISORY PLATFORM" in out
    assert "Available subcommands" in out


# ==============================================================================
# 2. DİM Score Calculator Tests
# ==============================================================================

def test_cli_dim_calc_direct_score():
    code, out = run_cli_args(["dim-calc", "--score", "655", "--group", "1", "--limit", "5"])
    assert code == 0
    assert "DİM Nəticə Hesabatı:" in out
    assert "655.0 / 700.0" in out
    assert "BANM 650+ TƏQAÜD BENCHMARKINI KEÇİR" in out
    assert "Tövsiyə Edilən İxtisaslar" in out


def test_cli_dim_calc_subexams():
    code, out = run_cli_args([
        "dim-calc", "--group", "1", "--sub-group", "ri",
        "--bur-closed", "60", "--bur-open", "15",
        "--blok-closed", "55", "--blok-open", "15",
        "--limit", "5"
    ])
    assert code == 0
    assert "DİM Nəticə Hesabatı:" in out
    assert "Buraxılış İmtahanı" in out
    assert "Blok İmtahanı" in out


def test_cli_dim_calc_json():
    code, out = run_cli_args(["--json", "dim-calc", "--score", "620", "--group", "1", "--limit", "3"])
    assert code == 0
    data = json.loads(out)
    assert data["score_breakdown"]["total_score"] == 620.0
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3


# ==============================================================================
# 3. Financial & Blocked Account Tests
# ==============================================================================

def test_cli_finance_germany_sperrkonto():
    code, out = run_cli_args(["finance", "--country", "DE", "--tuition", "0"])
    assert code == 0
    assert "Almaniya (§ 16b AufenthG) Sperrkonto Simulyasiyası:" in out
    assert "12,093.00" in out
    assert "992.00" in out
    assert "AZN Ekvivalenti:" in out


def test_cli_finance_uk_cas():
    code, out = run_cli_args(["finance", "--country", "GB", "--tuition", "15000"])
    assert code == 0
    assert "Böyük Britaniya (UKVI Appendix Student)" in out
    assert "28 Günlük Bank Tələbi:" in out


def test_cli_finance_all_destinations_benchmark():
    code, out = run_cli_args(["finance", "--all", "--budget-azn", "30000"])
    assert code == 0
    assert "4 Ölkə Üzrə Müqayisəli Maliyyə Simulyasiyası" in out
    assert "Germany" in out
    assert "United Kingdom" in out
    assert "United States" in out
    assert "Italy" in out


def test_cli_finance_json():
    code, out = run_cli_args(["--json", "finance", "--country", "DE"])
    assert code == 0
    data = json.loads(out)
    assert data["total_blocked_deposit_required"] == 12093.0
    assert "total_first_year_liquidity_azn" in data


# ==============================================================================
# 4. Global Scholarship Engine Tests
# ==============================================================================

def test_cli_scholarships_evaluation():
    code, out = run_cli_args(["scholarships", "--level", "master", "--gpa", "95", "--ielts", "7.5"])
    assert code == 0
    assert "Qlobal Təqaüd Qiymətləndirməsi" in out
    assert "Chevening Scholarship" in out
    assert "State Program on Foreign Education" in out
    assert "OPEN" in out


def test_cli_scholarships_filter_country():
    code, out = run_cli_args(["scholarships", "--country", "TR", "--level", "bachelor", "--age", "19"])
    assert code == 0
    assert "Türkiye Bursları" in out
    assert "OPEN" in out


def test_cli_scholarships_json():
    code, out = run_cli_args(["--json", "scholarships", "--country", "DE"])
    assert code == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["scholarship_key"] == "daad-germany"


# ==============================================================================
# 5. Admissions Timeline & Calendar Tests
# ==============================================================================

def test_cli_timeline_milestones():
    code, out = run_cli_args(["timeline", "--limit", "10"])
    assert code == 0
    assert "Qəbul & Təqaüd Dedlaynları 2026/2027" in out
    assert "Tarix" in out
    assert "Təcillilik" in out


def test_cli_timeline_urgency_filter():
    code, out = run_cli_args(["timeline", "--urgency", "critical"])
    assert code == 0
    assert "Qəbul & Təqaüd Dedlaynları 2026/2027" in out


def test_cli_timeline_json():
    code, out = run_cli_args(["--json", "timeline", "--limit", "5"])
    assert code == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) <= 5
    assert "target_date" in data[0]


# ==============================================================================
# 6. Multi-University Comparison Tests
# ==============================================================================

def test_cli_compare_benchmark_universities():
    code, out = run_cli_args(["compare", "--universities", "tum_cs,oxford_cs,rwth_engineering"])
    assert code == 0
    assert "Universitetlərin Çoxölçülü Müqayisə Matrisi:" in out
    assert "Technical University of Munich" in out
    assert "University of Oxford" in out
    assert "RWTH Aachen University" in out


def test_cli_compare_json():
    code, out = run_cli_args(["--json", "compare", "--universities", "tum_cs,oxford_cs"])
    assert code == 0
    data = json.loads(out)
    assert "lowest_cost_university" in data
    assert len(data["items"]) == 2


# ==============================================================================
# 7. Document Checklist Tests
# ==============================================================================

def test_cli_checklist_germany():
    code, out = run_cli_args(["checklist", "--country", "DE"])
    assert code == 0
    assert "Almaniya — Tələb Olunan Sənədlər Siyahısı" in out
    assert "Uni-Assist Vorprüfungsdokumentation (VPD)" in out
    assert "Sperrkonto" in out


def test_cli_checklist_state_programme():
    code, out = run_cli_args(["checklist", "--country", "DE", "--state-programme"])
    assert code == 0
    assert "Dövlət Proqramı Xüsusi Esse" in out


def test_cli_checklist_json():
    code, out = run_cli_args(["--json", "checklist", "--country", "GB"])
    assert code == 0
    data = json.loads(out)
    assert data["country_code"] == "GB"
    assert len(data["documents"]) >= 6


# ==============================================================================
# 8. Statement of Purpose (SOP) Audit Tests
# ==============================================================================

def test_cli_sop_check_default():
    code, out = run_cli_args(["sop-check"])
    assert code == 0
    assert "Statement of Purpose (SOP) Audit Nəticəsi:" in out
    assert "Ümumi Bal:" in out
    assert "Söz Sayı:" in out
    assert "Aşkar Edilmiş Qüsurlar və Şablonlar" in out


def test_cli_sop_check_json():
    text = (
        "I am writing to apply for the Master of Science in Computer Science. "
        "During my undergraduate studies in Baku, I conducted research on distributed systems. "
        "I published a paper on consensus algorithms and led an engineering team of 5 developers."
    )
    code, out = run_cli_args(["--json", "sop-check", "--text", text])
    assert code == 0
    data = json.loads(out)
    assert "overall_score" in data
    assert "letter_grade" in data
    assert data["word_count"] > 20


# ==============================================================================
# 9. Multi-Currency Converter Tests
# ==============================================================================

def test_cli_convert_currency():
    code, out = run_cli_args(["convert", "--amount", "1000", "--from", "EUR", "--to", "AZN", "--buffer", "2.5"])
    assert code == 0
    assert "AUSA Valyuta Konvertasiyası" in out
    assert "1,000.00 EUR" in out
    assert "1,900.35 AZN" in out


def test_cli_convert_json():
    code, out = run_cli_args(["--json", "convert", "--amount", "500", "--from", "USD", "--to", "AZN"])
    assert code == 0
    data = json.loads(out)
    assert data["amount"] == 500.0
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "AZN"
    assert data["exchange_rate"] == 1.7
    assert data["converted_amount"] == 850.0


# ==============================================================================
# 10. Document Legalisation & Recognition Process Tests
# ==============================================================================

def test_cli_process_curated_route():
    code, out = run_cli_args(["process", "--route", "de-bachelor-studienkolleg"])
    assert code == 0
    assert "ADMISSION ROUTE DOCUMENT LEGALISATION & RECOGNITION" in out
    assert "de-bachelor-studienkolleg" in out
    assert "CURATED" in out
    assert "Required Statutory Steps" in out
    assert "uni-assist" in out


def test_cli_process_not_collected_route():
    code, out = run_cli_args(["process", "--route", "uk-bachelor-direct"])
    assert code == 0
    assert "uk-bachelor-direct" in out
    assert "NOT_COLLECTED" in out
    assert "No curated legalisation steps recorded yet" in out


def test_cli_process_json_output():
    code, out = run_cli_args(["--json", "process", "--route", "tr-bachelor-direct"])
    assert code == 0
    data = json.loads(out)
    assert data["route_key"] == "tr-bachelor-direct"
    assert data["status"] == "curated"
    assert data["steps_count"] >= 1
    assert len(data["steps"]) >= 1
    assert "citation" in data["steps"][0]


def test_cli_process_unknown_route():
    code, out = run_cli_args(["process", "--route", "atlantis-phd-teleport"])
    assert code == 1
    assert "Unknown route key" in out

