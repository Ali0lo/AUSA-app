#!/usr/bin/env python3
"""
AUSA Developer & Admissions Command-Line Interface (CLI).

Provides unified terminal commands for admissions counseling, financial
simulations, DİM score calculations, scholarship evaluations, timeline
tracking, SOP auditing, and multi-university comparisons.

Usage:
    python -m backend.cli.ausa_cli --help
    python -m backend.cli.ausa_cli dim-calc --score 655 --group 1 --university BANM
    python -m backend.cli.ausa_cli finance --country DE --budget-azn 25000
    python -m backend.cli.ausa_cli scholarships --level master --gpa 92 --ielts 7.5
    python -m backend.cli.ausa_cli timeline --urgency critical
    python -m backend.cli.ausa_cli compare --universities tum_cs,oxford_cs,rwth_engineering
    python -m backend.cli.ausa_cli checklist --country DE
    python -m backend.cli.ausa_cli sop-check --text "My passion for technology started in childhood..."
"""

import argparse
import json
import os
import sys
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from app.domain.dim_calculator import (
        DimGroup,
        SubGroup,
        ChanceLevel,
        DimCalculationRequest,
        BuraxilisInput,
        BlokInput,
        SubjectQuestionInput,
        calculate_total_dim_score,
        get_specialty_recommendations,
    )
    from app.domain.financial_calculator import (
        Currency,
        UKLocationType,
        calculate_germany_funds,
        calculate_uk_funds,
        calculate_us_funds,
        calculate_italy_funds,
        compare_study_destinations_finance,
        convert_amount,
        get_exchange_rate,
    )
    from app.domain.global_scholarships import (
        ALL_GLOBAL_SCHOLARSHIPS,
        StudentScholarshipProfile,
        evaluate_scholarship,
        ScholarshipStatus,
    )
    from app.domain.timeline import (
        MilestoneFilter,
        get_timeline_schedule,
        UrgencyLevel,
        DegreeLevel,
    )
    from app.domain.application_tracker import (
        CURATED_COMPARISON_DB,
        ComparisonRequest,
        DocumentChecklistRequest,
        compare_universities,
        generate_document_checklist,
    )
    from app.domain.sop_analyzer import (
        SopAnalysisRequest,
        CvAnalysisRequest,
        analyze_sop_text,
        analyze_cv_text,
    )
except ImportError:
    from backend.app.domain.dim_calculator import (
        DimGroup,
        SubGroup,
        ChanceLevel,
        DimCalculationRequest,
        BuraxilisInput,
        BlokInput,
        SubjectQuestionInput,
        calculate_total_dim_score,
        get_specialty_recommendations,
    )
    from backend.app.domain.financial_calculator import (
        Currency,
        UKLocationType,
        calculate_germany_funds,
        calculate_uk_funds,
        calculate_us_funds,
        calculate_italy_funds,
        compare_study_destinations_finance,
        convert_amount,
        get_exchange_rate,
    )
    from backend.app.domain.global_scholarships import (
        ALL_GLOBAL_SCHOLARSHIPS,
        StudentScholarshipProfile,
        evaluate_scholarship,
        ScholarshipStatus,
    )
    from backend.app.domain.timeline import (
        MilestoneFilter,
        get_timeline_schedule,
        UrgencyLevel,
        DegreeLevel,
    )
    from backend.app.domain.application_tracker import (
        CURATED_COMPARISON_DB,
        ComparisonRequest,
        DocumentChecklistRequest,
        compare_universities,
        generate_document_checklist,
    )
    from backend.app.domain.sop_analyzer import (
        SopAnalysisRequest,
        CvAnalysisRequest,
        analyze_sop_text,
        analyze_cv_text,
    )

CLI_VERSION = "1.0.0"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
    ╔═══════════════════════════════════════════════════════════════╗
    ║       AUSA ADMISSIONS & UNIVERSITY ADVISORY PLATFORM          ║
    ║                   Developer & Student CLI                     ║
    ╚═══════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


# ==============================================================================
# Subcommand Handlers
# ==============================================================================

def cmd_dim_calc(args: argparse.Namespace) -> int:
    """Handles DİM 700-point calculation and historical specialty matching."""
    group_map = {
        1: DimGroup.GROUP_1,
        2: DimGroup.GROUP_2,
        3: DimGroup.GROUP_3,
        4: DimGroup.GROUP_4,
    }
    dim_group = group_map.get(args.group, DimGroup.GROUP_1)

    subgroup_map = {
        "rk": SubGroup.RK,
        "ri": SubGroup.RI,
        "dt": SubGroup.DT,
        "tc": SubGroup.TC,
    }
    dim_subgroup = subgroup_map.get(args.sub_group, SubGroup.RI)

    if args.score is not None:
        total_score = float(args.score)
        buraxilis_input = BuraxilisInput(direct_total_score=min(300.0, total_score * (300.0 / 700.0)))
        blok_input = BlokInput(direct_total_score=max(0.0, total_score - (total_score * (300.0 / 700.0))))
    else:
        buraxilis_input = BuraxilisInput(
            native_language=SubjectQuestionInput(
                subject_key="az", subject_name="Azərbaycan dili",
                closed_correct=args.bur_closed // 3, max_closed=25,
                open_points=float(args.bur_open // 3), max_open_points=10.0,
                max_scaled_points=100.0
            ),
            mathematics=SubjectQuestionInput(
                subject_key="math", subject_name="Riyaziyyat",
                closed_correct=args.bur_closed // 3, max_closed=25,
                open_points=float(args.bur_open // 3), max_open_points=10.0,
                max_scaled_points=100.0
            ),
            foreign_language=SubjectQuestionInput(
                subject_key="lang", subject_name="Xarici dil",
                closed_correct=args.bur_closed // 3, max_closed=25,
                open_points=float(args.bur_open // 3), max_open_points=10.0,
                max_scaled_points=100.0
            ),
        )
        blok_input = BlokInput(
            subject_1=SubjectQuestionInput(
                subject_key="b1", subject_name="Fənn 1",
                closed_correct=args.blok_closed // 3, max_closed=22,
                open_points=float(args.blok_open // 3), max_open_points=16.0,
                max_scaled_points=150.0
            ),
            subject_2=SubjectQuestionInput(
                subject_key="b2", subject_name="Fənn 2",
                closed_correct=args.blok_closed // 3, max_closed=22,
                open_points=float(args.blok_open // 3), max_open_points=16.0,
                max_scaled_points=150.0
            ),
            subject_3=SubjectQuestionInput(
                subject_key="b3", subject_name="Fənn 3",
                closed_correct=args.blok_closed // 3, max_closed=22,
                open_points=float(args.blok_open // 3), max_open_points=16.0,
                max_scaled_points=100.0
            ),
        )

    req = DimCalculationRequest(
        group=dim_group,
        subgroup=dim_subgroup,
        buraxilis=buraxilis_input,
        blok=blok_input,
    )
    score_breakdown = calculate_total_dim_score(req)

    # Force direct score if provided
    if args.score is not None:
        score_breakdown.total_score = float(args.score)

    rec_res = get_specialty_recommendations(
        score_breakdown=score_breakdown,
        university_filter=args.university,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(rec_res.model_dump(), indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}DİM Nəticə Hesabatı:{RESET}")
    print(f"  Qrup: {CYAN}{dim_group.value}{RESET} ({dim_subgroup.value})")
    print(f"  Toplam Bal: {GREEN}{BOLD}{score_breakdown.total_score:.1f} / 700.0{RESET}")
    print(f"  - Buraxılış İmtahanı: {score_breakdown.buraxilis_score:.1f} / 300.0")
    print(f"  - Blok İmtahanı: {score_breakdown.blok_score:.1f} / 400.0")
    if score_breakdown.clears_bhos_benchmark:
        print(f"  {MAGENTA}[BANM 650+ TƏQAÜD BENCHMARKINI KEÇİR]{RESET}")

    print(f"\n{BOLD}Tövsiyə Edilən İxtisaslar ({len(rec_res.recommendations)} nəticə):{RESET}")
    header = f"{'Universitet':<30} | {'İxtisas':<38} | {'2025 Bal':<8} | {'Şans':<12}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for r in rec_res.recommendations:
        tier_color = (
            GREEN if r.chance_level == ChanceLevel.SAFE
            else CYAN if r.chance_level == ChanceLevel.REALISTIC
            else YELLOW if r.chance_level == ChanceLevel.TARGET
            else RED
        )
        bhos_tag = f" {MAGENTA}[650+ BANM]{RESET}" if r.requires_650_rule else ""
        cutoff_str = f"{r.cutoff_2025:.0f}"

        print(
            f"{r.university_name[:30]:<30} | {r.department_name[:38]:<38} | {cutoff_str:<8} | "
            f"{tier_color}{r.chance_level.value:<12}{RESET}{bhos_tag}"
        )

    return 0


def cmd_finance(args: argparse.Namespace) -> int:
    """Handles blocked accounts and visa living cost simulations."""
    if args.all:
        comp = compare_study_destinations_finance(
            student_annual_budget_azn=args.budget_azn,
            tuition_eur=args.tuition,
            tuition_gbp=args.tuition,
            tuition_usd=args.tuition,
            tuition_italy_eur=args.tuition,
        )
        if args.json:
            payload = {
                "student_budget_azn": comp.student_budget_azn,
                "most_affordable_country": comp.most_affordable_country,
                "highest_liquidity_country": comp.highest_liquidity_country,
                "summary_verdict": comp.summary_verdict,
                "destinations": comp.destinations,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

        print(f"\n{BOLD}4 Ölkə Üzrə Müqayisəli Maliyyə Simulyasiyası (Büdcə: {args.budget_azn:,.2f} AZN):{RESET}\n")
        print(f"{comp.summary_verdict}\n")
        for d in comp.destinations:
            status_color = GREEN if d["is_within_budget"] else RED
            status_text = "KAFİDİR" if d["is_within_budget"] else "ÇATIŞMAZLIQ"
            print(f"{BOLD}{d['country']} ({d['currency']}):{RESET}")
            print(f"  Viza Kateqoriyası: {d['visa_category']}")
            print(f"  İlk İl Təxmini Cəmi Xərc: {d['total_first_year_cost_azn']:,.2f} AZN")
            print(f"  Vəziyyət: {status_color}{status_text}{RESET} ({d['budget_delta_azn']:+,.2f} AZN)")
            print(f"  Qayda: {d['key_regulatory_condition']}")
            print()
        return 0

    c = args.country.upper()
    if c == "DE":
        res = calculate_germany_funds(months=12, tuition_fee_eur=args.tuition)
        if args.json:
            print(json.dumps(res.__dict__, indent=2, ensure_ascii=False, default=str))
            return 0
        print(f"\n{BOLD}Almaniya (§ 16b AufenthG) Sperrkonto Simulyasiyası:{RESET}")
        print(f"  Rəsmi Bloklanmış Hesab: {YELLOW}€{res.total_blocked_deposit_required:,.2f}{RESET}")
        print(f"  Aylıq Sərbəst Buraxılan Məbləğ: €{res.statutory_monthly_amount:,.2f}")
        print(f"  İlk İl Təxmini Cəmi: {GREEN}€{res.total_first_year_liquidity_eur:,.2f}{RESET}")
        print(f"  AZN Ekvivalenti: {BOLD}{res.total_first_year_liquidity_azn:,.2f} AZN{RESET}")
    elif c == "GB":
        loc = UKLocationType.INNER_LONDON if args.london else UKLocationType.OUTSIDE_LONDON
        res = calculate_uk_funds(location_type=loc, course_tuition_annual_gbp=args.tuition)
        if args.json:
            print(json.dumps(res.__dict__, indent=2, ensure_ascii=False, default=str))
            return 0
        print(f"\n{BOLD}Böyük Britaniya (UKVI Appendix Student) Maintenance Funds:{RESET}")
        print(f"  28 Günlük Bank Tələbi: {YELLOW}£{res.total_funds_to_hold_28_days_gbp:,.2f}{RESET}")
        print(f"  9 Aylıq Yaşayış Xərci: £{res.maintenance_monthly_rate_gbp * 9:,.2f}")
        print(f"  IHS Sağlamlıq Sığortası: £{res.immigration_health_surcharge_gbp:,.2f}")
        print(f"  AZN Ekvivalenti: {BOLD}{res.total_funds_in_azn:,.2f} AZN{RESET}")
    elif c == "US":
        res = calculate_us_funds(tuition_annual_usd=args.tuition or 25000.0)
        if args.json:
            print(json.dumps(res.__dict__, indent=2, ensure_ascii=False, default=str))
            return 0
        print(f"\n{BOLD}ABŞ (Form I-20 COA) Maliyyə Tələbi:{RESET}")
        print(f"  Rəsmi I-20 Minimum: {YELLOW}${res.official_i20_total_usd:,.2f}{RESET}")
        print(f"  Tövsiyə Edilən Bank Çıxarışı (+15%): {GREEN}${res.total_recommended_affidavit_usd:,.2f}{RESET}")
        print(f"  AZN Ekvivalenti: {BOLD}{res.total_in_azn:,.2f} AZN{RESET}")
    else:
        res = calculate_italy_funds(
            family_members_count=args.members,
            family_annual_income_azn=args.iseeu_income,
            base_tuition_eur=args.tuition or 3500.0,
        )
        if args.json:
            print(json.dumps(res.__dict__, indent=2, ensure_ascii=False, default=str))
            return 0
        print(f"\n{BOLD}İtaliya (ISEE Parificato & DSU) Simulyasiyası:{RESET}")
        print(f"  Hesablanmış ISEE Parificato: {YELLOW}€{res.calculated_isee_parificato_eur:,.2f}{RESET}")
        print(f"  DSU Təqaüdü Təsdiqi: {GREEN if res.qualifies_for_dsu_fee_waiver else RED}{res.qualifies_for_dsu_fee_waiver}{RESET}")
        print(f"  Təxmini İllik Nağd Stipendiya: €{res.estimated_dsu_cash_stipend_eur:,.2f}")
        print(f"  Xalis İlk İl Xərci: {GREEN}€{res.net_first_year_cost_eur:,.2f}{RESET} ({res.net_first_year_cost_azn:,.2f} AZN)")

    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    """Handles multi-currency conversions using official CBAR benchmark rates."""
    from_curr = Currency(args.from_curr.upper())
    to_curr = Currency(args.to_curr.upper())
    converted = convert_amount(
        amount=args.amount,
        from_currency=from_curr,
        to_currency=to_curr,
        safety_buffer_pct=args.buffer,
    )
    rate = get_exchange_rate(from_curr, to_curr)

    if args.json:
        payload = {
            "amount": float(args.amount),
            "from_currency": from_curr.value,
            "to_currency": to_curr.value,
            "exchange_rate": float(rate),
            "safety_buffer_pct": float(args.buffer),
            "converted_amount": float(converted),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}AUSA Valyuta Konvertasiyası (Mərkəzi Bank CBAR Əsaslı):{RESET}")
    print(f"  Məbləğ: {args.amount:,.2f} {from_curr.value}")
    print(f"  Məzənnə (1 {from_curr.value} =): {rate:.4f} {to_curr.value}")
    if args.buffer > 0:
        print(f"  Təhlükəsizlik Buferi: +{args.buffer:.1f}%")
    print(f"  {GREEN}{BOLD}Yekun Məbləğ: {converted:,.2f} {to_curr.value}{RESET}\n")
    return 0


def cmd_scholarships(args: argparse.Namespace) -> int:
    """Evaluates candidate eligibility across 14 global scholarships."""
    profile = StudentScholarshipProfile(
        level_sought=args.level,
        age=args.age,
        gpa=args.gpa,
        ielts=args.ielts,
        work_experience_hours=args.work_hours,
        dim_score=float(args.dim_score) if args.dim_score else None,
        is_azerbaijani_citizen=True,
    )

    evaluations = []
    for s in ALL_GLOBAL_SCHOLARSHIPS:
        if args.country and s.country_code != args.country.upper():
            continue
        ev = evaluate_scholarship(s, profile)
        evaluations.append((s, ev))

    if args.json:
        payload = [
            {
                "scholarship_key": s.key,
                "name": s.name,
                "country": s.country_name,
                "status": ev.status.value,
                "summary_verdict": ev.summary_verdict,
                "gates_met": list(ev.gates_met),
                "gates_missing": list(ev.gates_missing),
                "gates_blocked": list(ev.gates_blocked),
            }
            for s, ev in evaluations
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}Qlobal Təqaüd Qiymətləndirməsi (Namizəd: GPA {args.gpa}, IELTS {args.ielts}, Dərəcə: {args.level}):{RESET}\n")

    for s, ev in evaluations:
        status_color = (
            GREEN if ev.status == ScholarshipStatus.OPEN
            else YELLOW if ev.status == ScholarshipStatus.UNLOCKABLE
            else RED
        )
        print(f"{BOLD}{s.name} ({s.country_name}):{RESET}")
        print(f"  Status: {status_color}{ev.status.value.upper()}{RESET}")
        print(f"  Təminat: {s.coverage_summary}")
        if ev.gates_missing:
            print("  Çatışmayan Şərtlər:")
            for m in ev.gates_missing:
                print(f"    - {m}")
        if ev.gates_blocked:
            print(f"  {RED}Bloklayan Səbəblər:{RESET}")
            for b in ev.gates_blocked:
                print(f"    - {b}")
        print()

    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    """Lists upcoming admissions milestones and application deadlines."""
    f = MilestoneFilter(
        country_code=args.country,
        degree_level=DegreeLevel(args.level) if args.level else None,
        urgency=UrgencyLevel(args.urgency.upper()) if args.urgency else None,
    )
    schedule = get_timeline_schedule(filters=f)
    milestones = schedule.milestones[:args.limit]

    if args.json:
        print(json.dumps([m.model_dump() for m in milestones], indent=2, ensure_ascii=False, default=str))
        return 0

    print(f"\n{BOLD}Qəbul & Təqaüd Dedlaynları 2026/2027 ({len(milestones)} nəticə):{RESET}\n")
    header = f"{'Tarix':<12} | {'Ölkə':<4} | {'Dedlayn / Portal':<42} | {'Qalan Gün':<10} | {'Təcillilik'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for m in milestones:
        urgency_color = (
            RED if m.urgency == UrgencyLevel.CRITICAL
            else YELLOW if m.urgency == UrgencyLevel.UPCOMING
            else GREEN if m.urgency == UrgencyLevel.OPEN
            else RESET
        )
        days_str = f"{m.days_remaining} gün" if m.days_remaining >= 0 else "Keçib"
        c_code = m.country_code.value if hasattr(m.country_code, "value") else str(m.country_code)
        print(
            f"{m.target_date.isoformat():<12} | {c_code:<4} | {m.title[:42]:<42} | "
            f"{days_str:<10} | {urgency_color}{m.urgency.value:<10}{RESET}"
        )

    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Generates side-by-side comparison matrix for universities."""
    uni_ids = [u.strip() for u in args.universities.split(",") if u.strip()]
    if not uni_ids:
        uni_ids = ["tum_cs", "oxford_cs", "rwth_engineering"]

    req = ComparisonRequest(
        university_ids=uni_ids,
        student_gpa=args.gpa,
        student_ielts=args.ielts,
    )
    res = compare_universities(req)

    if args.json:
        print(json.dumps(res.model_dump(), indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}Universitetlərin Çoxölçülü Müqayisə Matrisi:{RESET}")
    print(f"  Ən Sərfəli: {GREEN}{res.lowest_cost_university}{RESET}")
    print(f"  Ən Uzun İş Vizası: {CYAN}{res.longest_pswr_university}{RESET}")
    print(f"  Top Reytinqli: {YELLOW}{res.best_ranked_university}{RESET}")
    print(f"  Orta İllik Xərc: €{res.average_first_year_cost_eur:,.0f}\n")

    for item in res.items:
        print(f"{BOLD}• {item.university_name} ({item.city}, {item.country_code}):{RESET}")
        print(f"    Proqram: {item.program_name}")
        print(f"    İllik Təhsil Haqqı: €{item.tuition_eur_annual:,.0f} ({item.original_tuition})")
        print(f"    Aylıq Yaşayış Xərci: €{item.living_cost_eur_monthly:,.0f}")
        print(f"    Viza Bloklanmış Depozit: €{item.blocked_account_required_eur:,.0f}")
        print(f"    İlk İl Cəmi: {GREEN}€{item.total_first_year_eur:,.0f}{RESET}")
        print(f"    Məzun İş Vizası: {item.post_study_work_visa_duration_months} ay ({item.post_study_work_visa_name})")
        print(f"    Min. Tələblər: IELTS {item.ielts_min}")
        print()

    return 0


def cmd_checklist(args: argparse.Namespace) -> int:
    """Generates country-specific document checklist."""
    req = DocumentChecklistRequest(
        country_code=args.country,
        degree_level=args.level,
        is_state_programme=args.state_programme,
    )
    res = generate_document_checklist(req)

    if args.json:
        print(json.dumps(res.model_dump(), indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}{res.country_name} — Tələb Olunan Sənədlər Siyahısı ({res.total_documents} sənəd, {res.mandatory_count} mütləq):{RESET}\n")

    for idx, doc in enumerate(res.documents, start=1):
        mand_str = f"{RED}[Mütləq]{RESET}" if doc.is_mandatory else f"{YELLOW}[Seçimli]{RESET}"
        trans_str = "[Tərcümə]" if doc.translation_required else ""
        apos_str = "[Apostil]" if doc.apostille_required else ""
        flags = f"{mand_str} {trans_str} {apos_str}".strip()

        print(f"{idx}. {BOLD}{doc.title}{RESET} {flags}")
        print(f"   Açıqlama: {doc.description}")
        print(f"   Verən orqan: {doc.issuing_authority} | İcra müddəti: ~{doc.estimated_processing_days} gün\n")

    return 0


def cmd_sop_check(args: argparse.Namespace) -> int:
    """Audits Statement of Purpose for narrative structure and clichés."""
    text = ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        text = (
            "Ever since childhood, I have always had a deep passion for computer science. "
            "I want to think outside the box and create groundbreaking solutions. "
            "My academic journey at the university was shaped by hard work and determination. "
            "Studying at your esteemed faculty will allow me to achieve my long-term career goals."
        )

    req = SopAnalysisRequest(
        text=text,
        target_country=args.country,
        is_state_programme=args.state_programme,
    )
    res = analyze_sop_text(req)

    if args.json:
        print(json.dumps(res.model_dump(), indent=2, ensure_ascii=False))
        return 0

    print(f"\n{BOLD}Statement of Purpose (SOP) Audit Nəticəsi:{RESET}")
    score_color = GREEN if res.overall_score >= 80 else YELLOW if res.overall_score >= 60 else RED
    print(f"  Ümumi Bal: {score_color}{BOLD}{res.overall_score:.1f} / 100 ({res.letter_grade.value}){RESET}")
    print(f"  Qərar: {res.verdict}")
    print(f"  Söz Sayı: {res.word_count} söz ({res.reading_time_minutes:.1f} dəq oxu müddəti)")
    print(f"  Oxunaqlıq İndeksi (Flesch): {res.flesch_reading_ease:.1f} / 100")
    print(f"  Məchul Növ (Passive Voice) Sıxlığı: {res.passive_voice_percentage:.1f}%\n")

    print(f"{BOLD}Aşkar Edilmiş Qüsurlar və Şablonlar ({len(res.issues)} qeyd):{RESET}")
    for issue in res.issues:
        sev_color = RED if issue.severity.value == "CRITICAL" else YELLOW if issue.severity.value == "WARNING" else CYAN
        print(f"  • {sev_color}[{issue.severity.value}]{RESET} {issue.message}")
        if issue.suggestion:
            print(f"    Tövsiyə: {issue.suggestion}")

    return 0


# ==============================================================================
# Main Parser & CLI Entrypoint
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ausa",
        description="AUSA Admissions & University Advisory Platform Developer CLI",
    )
    parser.add_argument("--version", action="version", version=f"AUSA CLI v{CLI_VERSION}")
    parser.add_argument("--json", action="store_true", help="Format output as JSON")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. dim-calc
    p_dim = subparsers.add_parser("dim-calc", help="Calculate 700-point DİM score & recommend specialties")
    p_dim.add_argument("--group", type=int, choices=[1, 2, 3, 4], default=1, help="DİM exam group (1-4)")
    p_dim.add_argument("--sub-group", type=str, choices=["rk", "ri", "dt", "tc"], default="ri", help="Sub-group specialization")
    p_dim.add_argument("--score", type=float, help="Direct total DİM score (0-700)")
    p_dim.add_argument("--bur-closed", type=int, default=65, help="Buraxılış correct closed questions")
    p_dim.add_argument("--bur-open", type=int, default=15, help="Buraxılış correct open questions")
    p_dim.add_argument("--blok-closed", type=int, default=60, help="Blok correct closed questions")
    p_dim.add_argument("--blok-open", type=int, default=15, help="Blok correct open questions")
    p_dim.add_argument("--university", type=str, help="Filter cutoffs by university code (e.g. BANM, ADA, UNEC, BDU)")
    p_dim.add_argument("--limit", type=int, default=10, help="Max recommendation rows")

    # 2. finance
    p_fin = subparsers.add_parser("finance", help="Simulate blocked accounts and visa living costs")
    p_fin.add_argument("--country", type=str, choices=["DE", "GB", "US", "IT"], default="DE", help="Destination country")
    p_fin.add_argument("--tuition", type=float, default=0.0, help="Annual tuition in destination currency")
    p_fin.add_argument("--budget-azn", type=float, default=25000.0, help="Disposable first-year budget in AZN")
    p_fin.add_argument("--london", action="store_true", help="UK CAS: Inner London living cost")
    p_fin.add_argument("--members", type=int, default=4, help="Italy: Household members for ISEE-U")
    p_fin.add_argument("--iseeu-income", type=float, default=12000.0, help="Italy: Household annual net income AZN")
    p_fin.add_argument("--all", action="store_true", help="Benchmark all 4 destination countries")

    # 3. scholarships
    p_sch = subparsers.add_parser("scholarships", help="Evaluate candidate across 14 global scholarships")
    p_sch.add_argument("--level", type=str, choices=["bachelor", "master", "phd"], default="master", help="Degree level")
    p_sch.add_argument("--country", type=str, help="Filter scholarship by host country code (e.g. TR, GB, DE, IT)")
    p_sch.add_argument("--gpa", type=float, default=85.0, help="Academic GPA (0-100 scale)")
    p_sch.add_argument("--ielts", type=float, default=7.0, help="IELTS overall band score")
    p_sch.add_argument("--work-hours", type=int, default=2800, help="Verified work experience hours (for Chevening)")
    p_sch.add_argument("--age", type=int, default=23, help="Candidate age in years")
    p_sch.add_argument("--dim-score", type=int, default=655, help="DİM score (for BHOS full scholarship)")

    # 4. timeline
    p_time = subparsers.add_parser("timeline", help="List 2026/2027 admissions milestones & deadlines")
    p_time.add_argument("--country", type=str, help="Filter by country code (e.g. DE, GB, US, AZ, TR)")
    p_time.add_argument("--level", type=str, choices=["bachelor", "master", "phd"], help="Filter by degree level")
    p_time.add_argument("--urgency", type=str, choices=["critical", "upcoming", "open"], help="Filter by urgency tier")
    p_time.add_argument("--limit", type=int, default=15, help="Max milestones to display")

    # 5. compare
    p_comp = subparsers.add_parser("compare", help="Multi-university side-by-side comparison")
    p_comp.add_argument("--universities", type=str, default="tum_cs,oxford_cs,rwth_engineering", help="Comma-separated university IDs")
    p_comp.add_argument("--gpa", type=float, help="Student GPA percentage for tier classification")
    p_comp.add_argument("--ielts", type=float, help="Student IELTS score for tier classification")

    # 6. checklist
    p_chk = subparsers.add_parser("checklist", help="Generate prerequisite document checklist")
    p_chk.add_argument("--country", type=str, default="DE", help="Target country code (DE, GB, IT, TR, US)")
    p_chk.add_argument("--level", type=str, default="master", help="Degree level")
    p_chk.add_argument("--state-programme", action="store_true", help="Include State Programme requirement assets")

    # 7. sop-check
    p_sop = subparsers.add_parser("sop-check", help="Audit Statement of Purpose for narrative & clichés")
    p_sop.add_argument("--text", type=str, help="Raw text of Statement of Purpose")
    p_sop.add_argument("--file", type=str, help="Path to text or markdown file containing SOP")
    p_sop.add_argument("--country", type=str, default="DE", help="Destination country code")
    p_sop.add_argument("--state-programme", action="store_true", help="Include State Programme contribution check")

    # 8. convert
    p_conv = subparsers.add_parser("convert", help="Convert currencies with CBAR baseline rates & safety buffer")
    p_conv.add_argument("--amount", type=float, default=1000.0, help="Amount to convert")
    p_conv.add_argument("--from", dest="from_curr", type=str, default="EUR", choices=[c.value for c in Currency], help="Source currency (AZN, EUR, USD, GBP, TRY, PLN, HUF)")
    p_conv.add_argument("--to", dest="to_curr", type=str, default="AZN", choices=[c.value for c in Currency], help="Target currency (AZN, EUR, USD, GBP, TRY, PLN, HUF)")
    p_conv.add_argument("--buffer", type=float, default=0.0, help="Safety buffer percentage (e.g. 2.5 for 2.5%% cushion)")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        print_banner()
        parser.print_help()
        return 0

    handlers = {
        "dim-calc": cmd_dim_calc,
        "finance": cmd_finance,
        "convert": cmd_convert,
        "scholarships": cmd_scholarships,
        "timeline": cmd_timeline,
        "compare": cmd_compare,
        "checklist": cmd_checklist,
        "sop-check": cmd_sop_check,
    }

    handler = handlers.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
