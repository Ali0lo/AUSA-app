"""Domain logic for DİM (State Examination Center - Dövlət İmtahan Mərkəzi) score simulation.

Calculates authentic 700-point DİM scores in Azerbaijan:
- Buraxılış İmtahanı (Attestat graduation exam, max 300 points):
  * Ana dili (Azerbaijani/Russian, max 100)
  * Riyaziyyat (Mathematics, max 100)
  * Xarici dil (Foreign language, max 100)
- Blok İmtahanı (Specialty exam, max 400 points):
  * Group I (RK sub-group: Riyaziyyat 150, Fizika 150, Kimya 100)
  * Group I (Rİ sub-group: Riyaziyyat 150, Fizika 150, İnformatika 100)
  * Group II (Riyaziyyat 150, Coğrafiya 150, Tarix 100)
  * Group III (DT sub-group: Azərbaycan dili 150, Tarix 150, Ədəbiyyat 100)
  * Group III (TC sub-group: Azərbaycan dili 150, Tarix 150, Coğrafiya 100)
  * Group IV (Biologiya 150, Kimya 150, Fizika 100)
  * Group V (Buraxılış 300 + Qabiliyyət imtahanı)

Question Scoring Rules:
- Closed questions: 4 incorrect answers penalize 1 correct answer (net = max(0, correct - incorrect * 0.25)).
- Open / situational questions: Graded by raw points (no penalty).
- Supports direct known scores for students who already took Buraxılış or mock exams.
"""

from __future__ import annotations

import csv
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DimGroup(str, Enum):
    GROUP_1 = "I qrup"
    GROUP_2 = "II qrup"
    GROUP_3 = "III qrup"
    GROUP_4 = "IV qrup"
    GROUP_5 = "V qrup"


class SubGroup(str, Enum):
    # Group 1 sub-groups
    RK = "RK"  # Riyaziyyat - Kimya
    RI = "RI"  # Riyaziyyat - İnformatika
    # Group 3 sub-groups
    DT = "DT"  # Dil - Tarix
    TC = "TC"  # Tarix - Coğrafiya
    NONE = "NONE"


class ChanceLevel(str, Enum):
    SAFE = "SAFE"  # Score >= Cutoff + 30
    REALISTIC = "REALISTIC"  # Cutoff <= Score < Cutoff + 30
    TARGET = "TARGET"  # Cutoff - 35 <= Score < Cutoff
    ASPIRATIONAL = "ASPIRATIONAL"  # Score < Cutoff - 35


class SubjectQuestionInput(BaseModel):
    """Question breakdown for a single examination subject."""
    subject_key: str
    subject_name: str
    closed_correct: int = Field(default=0, ge=0, description="Correct closed answers")
    closed_incorrect: int = Field(default=0, ge=0, description="Incorrect closed answers (4 wrong = -1)")
    open_points: float = Field(default=0.0, ge=0.0, description="Points scored from open/situational questions")
    max_closed: int = Field(default=22, ge=1, description="Total closed questions")
    max_open_points: float = Field(default=16.0, ge=0.0, description="Maximum available open question points")
    max_scaled_points: float = Field(default=100.0, ge=1.0, description="Max subject score on DİM scale")
    direct_score: Optional[float] = Field(
        default=None, ge=0.0, description="Direct known score overriding question counts"
    )

    @field_validator("closed_correct")
    @classmethod
    def validate_closed_correct(cls, v: int, info: Any) -> int:
        max_c = info.data.get("max_closed", 30)
        if v > max_c:
            raise ValueError(f"Correct answers ({v}) cannot exceed maximum questions ({max_c})")
        return v

    @field_validator("closed_incorrect")
    @classmethod
    def validate_closed_incorrect(cls, v: int, info: Any) -> int:
        max_c = info.data.get("max_closed", 30)
        correct = info.data.get("closed_correct", 0)
        if v + correct > max_c:
            raise ValueError(f"Total answered questions ({v + correct}) cannot exceed max ({max_c})")
        return v


class SubjectScoreResult(BaseModel):
    """Calculated score breakdown for a single subject."""
    subject_key: str
    subject_name: str
    net_closed: float
    open_points: float
    total_raw: float
    max_raw: float
    scaled_score: float
    max_scaled: float
    percentage: float


class BuraxilisInput(BaseModel):
    """Inputs for the graduation examination (max 300 points)."""
    native_language: SubjectQuestionInput = Field(
        default_factory=lambda: SubjectQuestionInput(
            subject_key="native_language",
            subject_name="Tədris dili (Azərbaycan / Rus dili)",
            max_closed=20,
            max_open_points=20.0,
            max_scaled_points=100.0,
        )
    )
    mathematics: SubjectQuestionInput = Field(
        default_factory=lambda: SubjectQuestionInput(
            subject_key="mathematics",
            subject_name="Riyaziyyat",
            max_closed=13,
            max_open_points=19.0,  # 5 short open (1 mark) + 7 full open (2 marks) = 19
            max_scaled_points=100.0,
        )
    )
    foreign_language: SubjectQuestionInput = Field(
        default_factory=lambda: SubjectQuestionInput(
            subject_key="foreign_language",
            subject_name="Xarici dil (İngilis, Rus, Alman və s.)",
            max_closed=22,
            max_open_points=16.0,
            max_scaled_points=100.0,
        )
    )
    direct_total_score: Optional[float] = Field(
        default=None, ge=0.0, le=300.0, description="Direct total Buraxılış score if already known"
    )


class BlokInput(BaseModel):
    """Inputs for the specialty examination (max 400 points)."""
    subject_1: Optional[SubjectQuestionInput] = None
    subject_2: Optional[SubjectQuestionInput] = None
    subject_3: Optional[SubjectQuestionInput] = None
    direct_total_score: Optional[float] = Field(
        default=None, ge=0.0, le=400.0, description="Direct total Blok score if already known"
    )


class DimCalculationRequest(BaseModel):
    """Full payload for calculating a student's DİM score."""
    group: DimGroup = Field(default=DimGroup.GROUP_1, description="DİM İxtisas qrupu (I, II, III, IV, V)")
    subgroup: SubGroup = Field(default=SubGroup.RI, description="Sub-group specialization (RK/RI, DT/TC)")
    buraxilis: BuraxilisInput = Field(default_factory=BuraxilisInput)
    blok: Optional[BlokInput] = None


class DimScoreBreakdown(BaseModel):
    """Complete 700-point calculation breakdown."""
    group: DimGroup
    subgroup: SubGroup
    buraxilis_score: float = Field(ge=0.0, le=300.0)
    blok_score: float = Field(ge=0.0, le=400.0)
    total_score: float = Field(ge=0.0, le=700.0)
    max_total: float = 700.0
    percentage: float
    buraxilis_subjects: List[SubjectScoreResult]
    blok_subjects: List[SubjectScoreResult]
    clears_bhos_benchmark: bool = Field(
        description="True if candidate total score clears the 650.0 Baku Higher Oil School full state grant benchmark"
    )
    passed_competition_minimum: bool = Field(
        description="True if score passes the minimum 150 or 200 point competition threshold"
    )


class SpecialtyRecommendation(BaseModel):
    """Specialty matching result against historical DİM cutoffs."""
    program_code: str
    university_name: str
    department_name: str
    group_name: str
    scholarship_type: str  # "dövlət sifarişli"
    cutoff_2025: float
    cutoff_2024: Optional[float] = None
    cutoff_2023: Optional[float] = None
    three_year_trend: Optional[str] = None  # "+8.2", "-5.0", "stabil"
    candidate_score: float
    score_delta: float  # candidate_score - cutoff_2025
    chance_level: ChanceLevel
    is_bhos: bool
    requires_650_rule: bool


class DimRecommendationResponse(BaseModel):
    """Response containing calculated score and ranked eligible specialties."""
    score_breakdown: DimScoreBreakdown
    total_matched: int
    safe_count: int
    realistic_count: int
    target_count: int
    aspirational_count: int
    recommendations: List[SpecialtyRecommendation]


# Subject template constructors for each Group
def get_default_blok_input(group: DimGroup, subgroup: SubGroup = SubGroup.RI) -> BlokInput:
    """Returns official DİM subject configuration with correct maximum weights for each group."""
    if group == DimGroup.GROUP_1:
        if subgroup == SubGroup.RK:
            return BlokInput(
                subject_1=SubjectQuestionInput(
                    subject_key="math_g1",
                    subject_name="Riyaziyyat",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=150.0,
                ),
                subject_2=SubjectQuestionInput(
                    subject_key="physics_g1",
                    subject_name="Fizika",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=150.0,
                ),
                subject_3=SubjectQuestionInput(
                    subject_key="chemistry_g1",
                    subject_name="Kimya",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=100.0,
                ),
            )
        # Default to Rİ (Riyaziyyat - İnformatika)
        return BlokInput(
            subject_1=SubjectQuestionInput(
                subject_key="math_g1",
                subject_name="Riyaziyyat",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_2=SubjectQuestionInput(
                subject_key="physics_g1",
                subject_name="Fizika",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_3=SubjectQuestionInput(
                subject_key="informatics_g1",
                subject_name="İnformatika",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=100.0,
            ),
        )

    elif group == DimGroup.GROUP_2:
        return BlokInput(
            subject_1=SubjectQuestionInput(
                subject_key="math_g2",
                subject_name="Riyaziyyat",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_2=SubjectQuestionInput(
                subject_key="geography_g2",
                subject_name="Coğrafiya",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_3=SubjectQuestionInput(
                subject_key="history_g2",
                subject_name="Tarix",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=100.0,
            ),
        )

    elif group == DimGroup.GROUP_3:
        if subgroup == SubGroup.TC:
            return BlokInput(
                subject_1=SubjectQuestionInput(
                    subject_key="azerbaijani_g3",
                    subject_name="Azərbaycan dili",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=150.0,
                ),
                subject_2=SubjectQuestionInput(
                    subject_key="history_g3",
                    subject_name="Tarix",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=150.0,
                ),
                subject_3=SubjectQuestionInput(
                    subject_key="geography_g3",
                    subject_name="Coğrafiya",
                    max_closed=22,
                    max_open_points=16.0,
                    max_scaled_points=100.0,
                ),
            )
        # Default to DT (Dil - Tarix)
        return BlokInput(
            subject_1=SubjectQuestionInput(
                subject_key="azerbaijani_g3",
                subject_name="Azərbaycan dili",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_2=SubjectQuestionInput(
                subject_key="history_g3",
                subject_name="Tarix",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_3=SubjectQuestionInput(
                subject_key="literature_g3",
                subject_name="Ədəbiyyat",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=100.0,
            ),
        )

    elif group == DimGroup.GROUP_4:
        return BlokInput(
            subject_1=SubjectQuestionInput(
                subject_key="biology_g4",
                subject_name="Biologiya",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_2=SubjectQuestionInput(
                subject_key="chemistry_g4",
                subject_name="Kimya",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=150.0,
            ),
            subject_3=SubjectQuestionInput(
                subject_key="physics_g4",
                subject_name="Fizika",
                max_closed=22,
                max_open_points=16.0,
                max_scaled_points=100.0,
            ),
        )

    # Group 5 has no standard 3-subject block test; scored on Buraxılış + Qabiliyyət
    return BlokInput(
        subject_1=SubjectQuestionInput(
            subject_key="qabiliyyet_g5",
            subject_name="Qabiliyyət imtahanı",
            max_closed=0,
            max_open_points=100.0,
            max_scaled_points=100.0,
        ),
        subject_2=SubjectQuestionInput(
            subject_key="qabiliyyet_reserve",
            subject_name="Xüsusi normativ",
            max_closed=0,
            max_open_points=100.0,
            max_scaled_points=100.0,
        ),
    )


def calculate_subject_score(inp: SubjectQuestionInput) -> SubjectScoreResult:
    """Calculates the scaled score for one subject adhering to DİM 4-wrong penalty rules."""
    if inp.direct_score is not None:
        capped_direct = min(inp.direct_score, inp.max_scaled_points)
        capped_direct = max(0.0, capped_direct)
        percentage = round((capped_direct / inp.max_scaled_points) * 100.0, 1)
        return SubjectScoreResult(
            subject_key=inp.subject_key,
            subject_name=inp.subject_name,
            net_closed=0.0,
            open_points=0.0,
            total_raw=capped_direct,
            max_raw=inp.max_scaled_points,
            scaled_score=round(capped_direct, 1),
            max_scaled=inp.max_scaled_points,
            percentage=percentage,
        )

    # 4 incorrect answers subtract 1 correct answer
    net_closed = max(0.0, float(inp.closed_correct) - (float(inp.closed_incorrect) * 0.25))
    capped_open = min(float(inp.open_points), float(inp.max_open_points))
    total_raw = net_closed + capped_open
    max_raw = float(inp.max_closed) + float(inp.max_open_points)

    if max_raw <= 0.0:
        scaled = 0.0
    else:
        scaled = (total_raw / max_raw) * inp.max_scaled_points

    scaled = max(0.0, min(scaled, inp.max_scaled_points))
    percentage = round((scaled / inp.max_scaled_points) * 100.0, 1) if inp.max_scaled_points > 0 else 0.0

    return SubjectScoreResult(
        subject_key=inp.subject_key,
        subject_name=inp.subject_name,
        net_closed=round(net_closed, 2),
        open_points=round(capped_open, 1),
        total_raw=round(total_raw, 2),
        max_raw=round(max_raw, 1),
        scaled_score=round(scaled, 1),
        max_scaled=inp.max_scaled_points,
        percentage=percentage,
    )


def calculate_total_dim_score(req: DimCalculationRequest) -> DimScoreBreakdown:
    """Calculates full 700-point DİM score across Buraxılış and Blok components."""
    # 1. Buraxılış calculations
    buraxilis_subjects = [
        calculate_subject_score(req.buraxilis.native_language),
        calculate_subject_score(req.buraxilis.mathematics),
        calculate_subject_score(req.buraxilis.foreign_language),
    ]

    if req.buraxilis.direct_total_score is not None:
        buraxilis_total = min(300.0, max(0.0, req.buraxilis.direct_total_score))
    else:
        buraxilis_total = sum(s.scaled_score for s in buraxilis_subjects)
        buraxilis_total = min(300.0, max(0.0, buraxilis_total))

    # 2. Blok calculations
    blok_inp = req.blok or get_default_blok_input(req.group, req.subgroup)
    blok_subjects: List[SubjectScoreResult] = []

    if blok_inp.subject_1:
        blok_subjects.append(calculate_subject_score(blok_inp.subject_1))
    if blok_inp.subject_2:
        blok_subjects.append(calculate_subject_score(blok_inp.subject_2))
    if blok_inp.subject_3:
        blok_subjects.append(calculate_subject_score(blok_inp.subject_3))

    if blok_inp.direct_total_score is not None:
        blok_total = min(400.0, max(0.0, blok_inp.direct_total_score))
    else:
        blok_total = sum(s.scaled_score for s in blok_subjects)
        blok_total = min(400.0, max(0.0, blok_total))

    total_score = round(min(700.0, buraxilis_total + blok_total), 1)
    percentage = round((total_score / 700.0) * 100.0, 1)

    # 150 points minimum for paid admission; 200 points for state-funded competition
    passed_competition = total_score >= 150.0
    clears_bhos = total_score >= 650.0

    return DimScoreBreakdown(
        group=req.group,
        subgroup=req.subgroup,
        buraxilis_score=round(buraxilis_total, 1),
        blok_score=round(blok_total, 1),
        total_score=total_score,
        max_total=700.0,
        percentage=percentage,
        buraxilis_subjects=buraxilis_subjects,
        blok_subjects=blok_subjects,
        clears_bhos_benchmark=clears_bhos,
        passed_competition_minimum=passed_competition,
    )


# In-memory cached dataset from azerbaijan_cutoff_history.csv
_CACHED_CUTOFF_SERIES: Optional[List[Dict[str, Any]]] = None


def load_cutoff_history_records() -> List[Dict[str, Any]]:
    """Loads and caches 2,578 historical DİM cutoff records from CSV for offline/instant evaluation."""
    global _CACHED_CUTOFF_SERIES
    if _CACHED_CUTOFF_SERIES is not None:
        return _CACHED_CUTOFF_SERIES

    csv_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "azerbaijan_cutoff_history.csv"
    records: List[Dict[str, Any]] = []

    if not csv_path.exists():
        _CACHED_CUTOFF_SERIES = []
        return []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                val = float(row["cutoff_value"])
                year = int(row["intake_year"])
                records.append({
                    "program_code": row["source_program_code"],
                    "university_name": row["university_name"],
                    "department_name": row.get("department_name") or "",
                    "score_type": row.get("score_type") or "",
                    "scholarship_type": row.get("scholarship_type") or "dövlət sifarişli",
                    "intake_year": year,
                    "cutoff_value": val,
                })
            except (ValueError, KeyError):
                continue

    _CACHED_CUTOFF_SERIES = records
    return _CACHED_CUTOFF_SERIES


def get_specialty_recommendations(
    score_breakdown: DimScoreBreakdown,
    records: Optional[List[Dict[str, Any]]] = None,
    university_filter: Optional[str] = None,
    chance_filter: Optional[ChanceLevel] = None,
    search_query: Optional[str] = None,
    limit: int = 50,
) -> DimRecommendationResponse:
    """Matches a candidate's calculated DİM score against historical cutoffs, organizing into chance tiers."""
    all_records = records if records is not None else load_cutoff_history_records()
    target_group_str = score_breakdown.group.value  # e.g. "I qrup"

    # Group records by program_code to extract 2025, 2024, 2023 values
    programs_map: Dict[str, Dict[str, Any]] = {}
    for r in all_records:
        if r["score_type"] != target_group_str:
            continue

        pcode = r["program_code"]
        if pcode not in programs_map:
            is_bhos = "Baku Higher Oil School" in r["university_name"] or "BANM" in r["university_name"]
            programs_map[pcode] = {
                "program_code": pcode,
                "university_name": r["university_name"],
                "department_name": r["department_name"],
                "group_name": r["score_type"],
                "scholarship_type": r["scholarship_type"],
                "years": {},
                "is_bhos": is_bhos,
            }
        programs_map[pcode]["years"][r["intake_year"]] = r["cutoff_value"]

    recommendations: List[SpecialtyRecommendation] = []
    safe_c = realistic_c = target_c = aspirational_c = 0

    cand_score = score_breakdown.total_score

    for p in programs_map.values():
        c25 = p["years"].get(2025)
        c24 = p["years"].get(2024)
        c23 = p["years"].get(2023)

        requires_650_rule = False
        if c25 is None:
            if p["is_bhos"]:
                c25 = 650.0
                requires_650_rule = True
            elif c24 is not None:
                c25 = c24
            elif c23 is not None:
                c25 = c23
            else:
                continue

        # Check university filter
        if university_filter and university_filter.lower() not in p["university_name"].lower():
            continue

        # Check search query
        if search_query:
            q = search_query.lower()
            if q not in p["department_name"].lower() and q not in p["university_name"].lower():
                continue

        delta = round(cand_score - c25, 1)

        # Categorize chance level
        if delta >= 30.0:
            chance = ChanceLevel.SAFE
            safe_c += 1
        elif delta >= 0.0:
            chance = ChanceLevel.REALISTIC
            realistic_c += 1
        elif delta >= -35.0:
            chance = ChanceLevel.TARGET
            target_c += 1
        else:
            chance = ChanceLevel.ASPIRATIONAL
            aspirational_c += 1

        if chance_filter and chance != chance_filter:
            continue

        # Compute trend
        trend_str: Optional[str] = None
        if c25 is not None and c24 is not None:
            t_diff = round(c25 - c24, 1)
            if t_diff > 0:
                trend_str = f"+{t_diff}"
            elif t_diff < 0:
                trend_str = f"{t_diff}"
            else:
                trend_str = "stabil"

        recommendations.append(
            SpecialtyRecommendation(
                program_code=p["program_code"],
                university_name=p["university_name"],
                department_name=p["department_name"],
                group_name=p["group_name"],
                scholarship_type=p["scholarship_type"],
                cutoff_2025=c25,
                cutoff_2024=c24,
                cutoff_2023=c23,
                three_year_trend=trend_str,
                candidate_score=cand_score,
                score_delta=delta,
                chance_level=chance,
                is_bhos=p["is_bhos"],
                requires_650_rule=requires_650_rule,
            )
        )

    # Sort: Safe -> Realistic -> Target -> Aspirational; within tier by delta descending
    tier_order = {
        ChanceLevel.SAFE: 0,
        ChanceLevel.REALISTIC: 1,
        ChanceLevel.TARGET: 2,
        ChanceLevel.ASPIRATIONAL: 3,
    }
    recommendations.sort(key=lambda x: (tier_order[x.chance_level], -x.cutoff_2025))

    return DimRecommendationResponse(
        score_breakdown=score_breakdown,
        total_matched=len(recommendations),
        safe_count=safe_c,
        realistic_count=realistic_c,
        target_count=target_c,
        aspirational_count=aspirational_c,
        recommendations=recommendations[:limit],
    )


def get_all_dim_group_metadata() -> List[Dict[str, Any]]:
    """Returns statutory structure and subject weights for all 5 DİM groups."""
    return [
        {
            "group": DimGroup.GROUP_1.value,
            "name": "I İxtisas Qrupu",
            "description": "Dəqiq və texniki elmlər, mühəndislik, IT və kompüter elmləri",
            "subgroups": [
                {
                    "code": SubGroup.RI.value,
                    "name": "Riyaziyyat - İnformatika (Rİ)",
                    "subjects": ["Riyaziyyat (150 bal)", "Fizika (150 bal)", "İnformatika (100 bal)"],
                },
                {
                    "code": SubGroup.RK.value,
                    "name": "Riyaziyyat - Kimya (RK)",
                    "subjects": ["Riyaziyyat (150 bal)", "Fizika (150 bal)", "Kimya (100 bal)"],
                },
            ],
            "max_buraxilis": 300,
            "max_blok": 400,
            "max_total": 700,
        },
        {
            "group": DimGroup.GROUP_2.value,
            "name": "II İxtisas Qrupu",
            "description": "İqtisadiyyat, idarəetmə, maliyyə, biznes və beynəlxalq münasibətlər",
            "subgroups": [
                {
                    "code": SubGroup.NONE.value,
                    "name": "Standart",
                    "subjects": ["Riyaziyyat (150 bal)", "Coğrafiya (150 bal)", "Tarix (100 bal)"],
                }
            ],
            "max_buraxilis": 300,
            "max_blok": 400,
            "max_total": 700,
        },
        {
            "group": DimGroup.GROUP_3.value,
            "name": "III İxtisas Qrupu",
            "description": "Humanitar, filologiya, hüquqşünaslıq, təhsil və pedaqogika",
            "subgroups": [
                {
                    "code": SubGroup.DT.value,
                    "name": "Dil - Tarix (DT)",
                    "subjects": ["Azərbaycan dili (150 bal)", "Tarix (150 bal)", "Ədəbiyyat (100 bal)"],
                },
                {
                    "code": SubGroup.TC.value,
                    "name": "Tarix - Coğrafiya (TC)",
                    "subjects": ["Azərbaycan dili (150 bal)", "Tarix (150 bal)", "Coğrafiya (100 bal)"],
                },
            ],
            "max_buraxilis": 300,
            "max_blok": 400,
            "max_total": 700,
        },
        {
            "group": DimGroup.GROUP_4.value,
            "name": "IV İxtisas Qrupu",
            "description": "Təbii və tibb elmləri: Tibb, stomatologiya, əczaçılıq, biologiya, kimya",
            "subgroups": [
                {
                    "code": SubGroup.NONE.value,
                    "name": "Standart",
                    "subjects": ["Biologiya (150 bal)", "Kimya (150 bal)", "Fizika (100 bal)"],
                }
            ],
            "max_buraxilis": 300,
            "max_blok": 400,
            "max_total": 700,
        },
        {
            "group": DimGroup.GROUP_5.value,
            "name": "V İxtisas Qrupu",
            "description": "Xüsusi qabiliyyət tələb edən ixtisaslar (Musiqi, incəsənət, dizayn, idman)",
            "subgroups": [
                {
                    "code": SubGroup.NONE.value,
                    "name": "Buraxılış + Qabiliyyət",
                    "subjects": ["Buraxılış imtahanı (300 bal)", "Xüsusi Qabiliyyət imtahanı"],
                }
            ],
            "max_buraxilis": 300,
            "max_blok": 100,
            "max_total": 400,
        },
    ]
