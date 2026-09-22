"""Domain logic for Statement of Purpose (SOP) & Academic CV rubric evaluation.

Provides rule-based heuristic auditing tailored for Azerbaijani applicants applying
to foreign universities and competitive bilateral scholarships (State Programme 2022-2026,
Chevening, Fulbright, DAAD, Türkiye Bursları, Stipendium Hungaricum, etc.).

Evaluates:
- Word count bounds, paragraph pacing, and readability (Flesch Reading Ease).
- Cliché detection with targeted academic replacements.
- Passive voice frequency and weak phrasing.
- Core narrative section presence:
  1. Intellectual Hook & Motivation
  2. Academic & Research Foundation
  3. Why This Specific University & Faculty
  4. Short- & Long-Term Career Objectives
  5. Bilateral / Azerbaijan National Contribution Clause (State Programme requirement)
- Academic CV structure (Europass & US graduate standards), bullet action verbs, and quantification.
"""

from __future__ import annotations

import math
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"
    GOOD = "GOOD"


class SectionStatus(str, Enum):
    STRONG = "STRONG"
    PRESENT = "PRESENT"
    WEAK = "WEAK"
    MISSING = "MISSING"


class LetterGrade(str, Enum):
    A = "A"  # 85 - 100: Outstanding
    B = "B"  # 70 - 84: Strong
    C = "C"  # 50 - 69: Needs Work
    D = "D"  # < 50: Major Revision Required


class WritingIssue(BaseModel):
    """Specific writing issue detected in the essay or CV."""
    id: str
    category: str  # "Cliche", "Passive Voice", "Length", "Structure", "Content"
    severity: IssueSeverity
    message: str
    matched_text: Optional[str] = None
    suggestion: Optional[str] = None
    line_number: Optional[int] = None


class SectionMatch(BaseModel):
    """Evaluation of a mandatory SOP or CV narrative section."""
    section_key: str
    name: str
    status: SectionStatus
    score: float
    max_score: float
    detected_phrases: List[str] = Field(default_factory=list)
    feedback: str


class SopAnalysisRequest(BaseModel):
    """Input payload for SOP evaluation."""
    text: str = Field(min_length=10, description="Full Statement of Purpose text")
    target_degree: str = Field(default="master", description="bachelor, master, or phd")
    target_field: str = Field(default="stem", description="stem, business, humanities, law")
    word_limit_min: int = Field(default=500, ge=100, le=2000)
    word_limit_max: int = Field(default=1000, ge=200, le=3000)
    is_state_programme: bool = Field(
        default=True,
        description="Whether applicant intends to apply for the Azerbaijan State Programme 2022-2026",
    )


class SopAnalysisResult(BaseModel):
    """Comprehensive evaluation result for a Statement of Purpose."""
    overall_score: float = Field(ge=0.0, le=100.0)
    letter_grade: LetterGrade
    verdict: str
    word_count: int
    char_count: int
    paragraph_count: int
    average_sentence_length: float
    reading_time_minutes: float
    flesch_reading_ease: float
    passive_voice_percentage: float
    lexical_diversity: float
    category_scores: Dict[str, float]
    sections: List[SectionMatch]
    issues: List[WritingIssue]
    strengths: List[str]


class CvAnalysisRequest(BaseModel):
    """Input payload for Academic CV / Resume analysis."""
    text: str = Field(min_length=20, description="Full CV / Resume plain text")
    target_format: str = Field(default="standard_academic", description="europass, standard_academic, us_graduate")


class CvAnalysisResult(BaseModel):
    """Comprehensive audit for an Academic CV."""
    overall_score: float = Field(ge=0.0, le=100.0)
    letter_grade: LetterGrade
    verdict: str
    word_count: int
    bullet_count: int
    quantified_bullets_count: int
    action_verb_bullets_count: int
    sections_detected: List[str]
    missing_sections: List[str]
    issues: List[WritingIssue]
    strengths: List[str]


class SopTemplate(BaseModel):
    """Curated exemplary Statement of Purpose framework."""
    id: str
    title: str
    degree_level: str
    field: str
    description: str
    content: str
    word_count: int


# Curated cliché dictionary with precise academic alternatives
CLICHE_PATTERNS = [
    (
        r"\b(ever since I was a (child|kid|young (boy|girl))|since my childhood|from an early age|since my youth)\b",
        "Childhood Cliché Opening",
        "Admissions committees recommend against starting with childhood anecdotes. Open directly with a mature intellectual turning point or your specific undergraduate research question.",
    ),
    (
        r"\b(I have always been passionate about|I am passionate about|my passion for)\b",
        "Overused 'Passion' Trope",
        "Instead of telling the reader you are 'passionate', demonstrate it with tangible evidence: 'My dedication to machine learning culminated in my capstone project analyzing...'",
    ),
    (
        r"\b(allow me to introduce myself|my name is)\b",
        "Conversational Greeting",
        "Do not introduce yourself in the first line. Your name is already on your application file; use your opening sentence for your core research statement.",
    ),
    (
        r"\b(it has always been my dream|my lifelong dream|dream come true)\b",
        "Dream Trope",
        "Frame your application around structured academic goals and research objectives rather than emotional dreams.",
    ),
    (
        r"\b(in today'?s (globalized|modern|fast-paced) world|in the era of globalization)\b",
        "Generic Global Context Fluff",
        "Avoid sweeping universal statements. Ground your motivation in specific contemporary challenges in your discipline.",
    ),
    (
        r"\b(webster'?s? dictionary defines|oxford dictionary defines|dictionary defines)\b",
        "Dictionary Definition Opening",
        "Starting with a dictionary definition is considered an amateur rhetorical device. Replace it with your own analytical perspective.",
    ),
    (
        r"\b(I am a hardworking(,| and) (punctual|motivated|dedicated) individual)\b",
        "Resume Buzzword Cliché",
        "Show these qualities through verifiable achievements rather than self-declarative adjective lists.",
    ),
    (
        r"\b(sky is the limit|think outside the box|at the end of the day)\b",
        "Casual Idiom",
        "Replace colloquial idioms with precise academic exposition.",
    ),
    (
        r"\b(paragon of excellence|world-class faculty|renowned institution)\b",
        "Unsubstantiated Flattery",
        "Committees recognize generic praise. Name specific professors, research groups, or curriculum modules unique to this university.",
    ),
    (
        r"\b(broaden my horizons|expand my knowledge)\b",
        "Vague Learning Cliché",
        "Specify the exact methodologies, advanced theories, or laboratory tools you intend to master.",
    ),
]

# Action verbs that strengthen academic and professional writing
STRONG_ACTION_VERBS = {
    "spearheaded", "engineered", "designed", "implemented", "synthesized",
    "orchestrated", "quantified", "analyzed", "formulated", "published",
    "developed", "investigated", "evaluated", "optimized", "modeled",
    "constructed", "streamlined", "calculated", "demonstrated", "pioneered",
    "automated", "executed", "derived", "architected", "simulated",
}

# Regex for detecting passive voice: auxiliary 'to be' + past participle
PASSIVE_VOICE_REGEX = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en|conducted|performed|built|written|made|undertaken|analyzed|researched)\b",
    re.IGNORECASE,
)


def calculate_flesch_reading_ease(text: str) -> float:
    """Calculates Flesch Reading Ease score.

    Score ~ 40 - 65 is ideal for academic graduate essays.
    """
    words = re.findall(r"\b[A-Za-z]+\b", text)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not words or not sentences:
        return 50.0

    total_words = len(words)
    total_sentences = max(1, len(sentences))

    # Syllable approximation
    def count_syllables(w: str) -> int:
        w = w.lower()
        count = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and not w.endswith("le") and count > 1:
            count -= 1
        return max(1, count)

    total_syllables = sum(count_syllables(w) for w in words)

    score = 206.835 - (1.015 * (total_words / total_sentences)) - (84.6 * (total_syllables / total_words))
    return round(max(0.0, min(100.0, score)), 1)


def analyze_sop_text(req: SopAnalysisRequest) -> SopAnalysisResult:
    """Analyzes a Statement of Purpose against academic rubric and State Programme requirements."""
    raw_text = req.text.strip()
    words = re.findall(r"\b[\w'-]+\b", raw_text)
    word_count = len(words)
    char_count = len(raw_text)

    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1 and "\n" in raw_text:
        paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
    paragraph_count = max(1, len(paragraphs))

    sentences = [s.strip() for s in re.split(r"[.!?]+", raw_text) if len(s.strip().split()) > 2]
    total_sentences = max(1, len(sentences))
    avg_sentence_len = round(word_count / total_sentences, 1)

    # Reading time (avg 220 words per minute for admissions readers)
    reading_time = round(word_count / 220.0, 1)

    # Flesch reading ease
    flesch_score = calculate_flesch_reading_ease(raw_text)

    # Lexical diversity (Type-Token Ratio)
    unique_words = {w.lower() for w in words if len(w) > 2}
    lexical_diversity = round((len(unique_words) / max(1, word_count)) * 100.0, 1)

    issues: List[WritingIssue] = []
    strengths: List[str] = []

    # 1. Length & Hygiene Audit (Max 20 pts)
    length_score = 20.0
    if word_count < req.word_limit_min:
        deficit = req.word_limit_min - word_count
        penalty = min(15.0, (deficit / 100.0) * 5.0)
        length_score -= penalty
        issues.append(
            WritingIssue(
                id="length_under",
                category="Length",
                severity=IssueSeverity.CRITICAL if deficit > 150 else IssueSeverity.WARNING,
                message=f"Essay is under the minimum recommendation ({word_count} / {req.word_limit_min} words).",
                suggestion=f"Expand your academic context or specific laboratory goals by {deficit} words.",
            )
        )
    elif word_count > req.word_limit_max:
        excess = word_count - req.word_limit_max
        penalty = min(12.0, (excess / 100.0) * 4.0)
        length_score -= penalty
        issues.append(
            WritingIssue(
                id="length_over",
                category="Length",
                severity=IssueSeverity.WARNING,
                message=f"Essay exceeds the target maximum ({word_count} / {req.word_limit_max} words).",
                suggestion=f"Trim redundant adverbs and background descriptions by {excess} words to respect committee attention.",
            )
        )
    else:
        strengths.append(f"Optimal word count ({word_count} words), fully compliant with target limit.")

    if paragraph_count < 3:
        length_score -= 4.0
        issues.append(
            WritingIssue(
                id="paragraphs_few",
                category="Structure",
                severity=IssueSeverity.WARNING,
                message=f"Essay has only {paragraph_count} paragraphs. Text blocks become difficult to read.",
                suggestion="Divide your narrative into 4-6 paragraphs: Introduction, Academic background, Why this university, Career goals, and Contribution.",
            )
        )
    elif 4 <= paragraph_count <= 7:
        strengths.append(f"Clean structural cadence across {paragraph_count} balanced paragraphs.")

    # 2. Cliché & Fluff Detection (Max 20 pts)
    cliche_score = 20.0
    found_cliches = 0
    for pattern, title, suggestion in CLICHE_PATTERNS:
        matches = list(re.finditer(pattern, raw_text, re.IGNORECASE))
        if matches:
            found_cliches += len(matches)
            for m in matches:
                issues.append(
                    WritingIssue(
                        id=f"cliche_{len(issues)}",
                        category="Cliche",
                        severity=IssueSeverity.CRITICAL if "Opening" in title or "Childhood" in title else IssueSeverity.WARNING,
                        message=f"{title}: '{m.group(0)}'",
                        matched_text=m.group(0),
                        suggestion=suggestion,
                    )
                )

    cliche_penalty = min(18.0, found_cliches * 4.5)
    cliche_score = max(0.0, cliche_score - cliche_penalty)
    if found_cliches == 0:
        strengths.append("Zero cliché formulaic phrases detected; mature, original academic voice.")

    # 3. Voice & Action Verb Density (Max 15 pts)
    passive_matches = list(PASSIVE_VOICE_REGEX.finditer(raw_text))
    passive_count = len(passive_matches)
    passive_pct = round((passive_count / total_sentences) * 100.0, 1)

    voice_score = 15.0
    if passive_pct > 25.0:
        voice_score -= 8.0
        issues.append(
            WritingIssue(
                id="voice_passive_high",
                category="Passive Voice",
                severity=IssueSeverity.WARNING,
                message=f"High passive voice frequency ({passive_pct}% of sentences).",
                suggestion="Rewrite passive structures into active voice to demonstrate personal agency (e.g. 'I designed' rather than 'was designed by me').",
            )
        )
    elif passive_pct < 15.0:
        strengths.append(f"Assertive active voice ({passive_pct}% passive ratio), showing clear individual initiative.")

    # Strong action verbs
    lowered_words = [w.lower() for w in words]
    action_verb_hits = sum(1 for w in lowered_words if w in STRONG_ACTION_VERBS)
    if action_verb_hits >= 5:
        strengths.append(f"Strong action verb presence ({action_verb_hits} dynamic verbs reinforcing technical capability).")
    else:
        issues.append(
            WritingIssue(
                id="action_verbs_low",
                category="Voice",
                severity=IssueSeverity.SUGGESTION,
                message="Consider incorporating more high-impact technical action verbs.",
                suggestion="Use verbs like 'engineered', 'spearheaded', 'synthesized', 'quantified', 'streamlined'.",
            )
        )

    # 4. Readability & Metrics (Max 10 pts)
    metrics_score = 10.0
    has_numbers = bool(re.search(r"\b(\d+(\.\d+)?%|\$\d+|\d+\+?)\b", raw_text))
    if has_numbers:
        strengths.append("Evidence of quantified impact with concrete metrics and data points.")
    else:
        metrics_score -= 3.0
        issues.append(
            WritingIssue(
                id="metrics_missing",
                category="Content",
                severity=IssueSeverity.SUGGESTION,
                message="Few or no quantified metrics found in essay.",
                suggestion="Strengthen your claims with numbers: project efficiency gains (e.g., 'improved throughput by 24%'), dataset size ('10,000 samples'), or team scale.",
            )
        )

    # 5. Core Narrative Sections (Max 35 pts)
    sections: List[SectionMatch] = []

    # Section 1: Hook & Motivation (7 pts)
    hook_keywords = ["inspire", "motivated", "turning point", "curiosity", "intrigued", "fascination", "sparked", "challenge"]
    hook_matches = [w for w in hook_keywords if re.search(r"\b" + w, raw_text, re.IGNORECASE)]
    if len(hook_matches) >= 2:
        sec_hook = SectionMatch(
            section_key="hook",
            name="Intellectual Hook & Motivation",
            status=SectionStatus.STRONG,
            score=7.0,
            max_score=7.0,
            detected_phrases=hook_matches[:4],
            feedback="Strong, purposeful motivation grounding your academic interest.",
        )
    elif hook_matches:
        sec_hook = SectionMatch(
            section_key="hook",
            name="Intellectual Hook & Motivation",
            status=SectionStatus.PRESENT,
            score=4.5,
            max_score=7.0,
            detected_phrases=hook_matches,
            feedback="Motivation is present but could connect more sharply to your intended field.",
        )
    else:
        sec_hook = SectionMatch(
            section_key="hook",
            name="Intellectual Hook & Motivation",
            status=SectionStatus.WEAK,
            score=2.0,
            max_score=7.0,
            detected_phrases=[],
            feedback="Opening lacks an intellectual catalyst explaining why you chose this path.",
        )
    sections.append(sec_hook)

    # Section 2: Academic & Research Foundation (8 pts)
    acad_keywords = ["bachelor", "undergraduate", "thesis", "research", "coursework", "gpa", "capstone", "project", "laboratory", "experiment"]
    acad_matches = [w for w in acad_keywords if re.search(r"\b" + w, raw_text, re.IGNORECASE)]
    if len(acad_matches) >= 3:
        sec_acad = SectionMatch(
            section_key="academic",
            name="Academic & Research Foundation",
            status=SectionStatus.STRONG,
            score=8.0,
            max_score=8.0,
            detected_phrases=acad_matches[:4],
            feedback="Clear technical substantiation from undergraduate coursework and research.",
        )
    elif acad_matches:
        sec_acad = SectionMatch(
            section_key="academic",
            name="Academic & Research Foundation",
            status=SectionStatus.PRESENT,
            score=5.0,
            max_score=8.0,
            detected_phrases=acad_matches,
            feedback="Mention specific undergraduate courses or thesis topics for greater credibility.",
        )
    else:
        sec_acad = SectionMatch(
            section_key="academic",
            name="Academic & Research Foundation",
            status=SectionStatus.MISSING,
            score=1.0,
            max_score=8.0,
            detected_phrases=[],
            feedback="Missing concrete details regarding your undergraduate background or research.",
        )
    sections.append(sec_acad)

    # Section 3: Why This University & Faculty (8 pts)
    univ_keywords = ["curriculum", "professor", "faculty", "laboratory", "module", "department", "program", "specialization", "course", "syllabus"]
    univ_matches = [w for w in univ_keywords if re.search(r"\b" + w, raw_text, re.IGNORECASE)]
    if len(univ_matches) >= 3:
        sec_univ = SectionMatch(
            section_key="university",
            name="Why This Specific University",
            status=SectionStatus.STRONG,
            score=8.0,
            max_score=8.0,
            detected_phrases=univ_matches[:4],
            feedback="Excellent institutional tailoring; references specific curriculum elements.",
        )
    elif univ_matches:
        sec_univ = SectionMatch(
            section_key="university",
            name="Why This Specific University",
            status=SectionStatus.WEAK,
            score=4.0,
            max_score=8.0,
            detected_phrases=univ_matches,
            feedback="Institutional rationale is somewhat generic. Name specific professors or lab facilities.",
        )
    else:
        sec_univ = SectionMatch(
            section_key="university",
            name="Why This Specific University",
            status=SectionStatus.MISSING,
            score=0.0,
            max_score=8.0,
            detected_phrases=[],
            feedback="Crucial omission: The essay could be submitted to any university. Tailor to this specific program.",
        )
    sections.append(sec_univ)

    # Section 4: Short- and Long-Term Career Roadmap (6 pts)
    career_keywords = ["career", "future", "aspire", "goal", "short-term", "long-term", "industry", "phd", "role", "position", "objective"]
    career_matches = [w for w in career_keywords if re.search(r"\b" + w, raw_text, re.IGNORECASE)]
    if len(career_matches) >= 3:
        sec_career = SectionMatch(
            section_key="career",
            name="Career Trajectory & Goals",
            status=SectionStatus.STRONG,
            score=6.0,
            max_score=6.0,
            detected_phrases=career_matches[:4],
            feedback="Well-articulated short-term and long-term professional roadmap.",
        )
    elif career_matches:
        sec_career = SectionMatch(
            section_key="career",
            name="Career Trajectory & Goals",
            status=SectionStatus.PRESENT,
            score=3.5,
            max_score=6.0,
            detected_phrases=career_matches,
            feedback="Mention specific post-graduation job titles, industries, or doctoral plans.",
        )
    else:
        sec_career = SectionMatch(
            section_key="career",
            name="Career Trajectory & Goals",
            status=SectionStatus.MISSING,
            score=0.0,
            max_score=6.0,
            detected_phrases=[],
            feedback="Missing clear post-graduation career objectives.",
        )
    sections.append(sec_career)

    # Section 5: Azerbaijan National / State Programme Contribution (6 pts)
    aze_keywords = ["azerbaijan", "baku", "home country", "national", "state programme", "economy", "repatriation", "contribution", "local industry", "region"]
    aze_matches = [w for w in aze_keywords if re.search(r"\b" + w, raw_text, re.IGNORECASE)]
    if req.is_state_programme:
        if len(aze_matches) >= 2:
            sec_aze = SectionMatch(
                section_key="azerbaijan_contribution",
                name="Contribution to Azerbaijan (State Programme)",
                status=SectionStatus.STRONG,
                score=6.0,
                max_score=6.0,
                detected_phrases=aze_matches[:4],
                feedback="Clear repatriation plan outlining know-how transfer to Azerbaijan.",
            )
        elif aze_matches:
            sec_aze = SectionMatch(
                section_key="azerbaijan_contribution",
                name="Contribution to Azerbaijan (State Programme)",
                status=SectionStatus.PRESENT,
                score=3.5,
                max_score=6.0,
                detected_phrases=aze_matches,
                feedback="Mention how your foreign study directly addresses priority sectors in Azerbaijan.",
            )
        else:
            sec_aze = SectionMatch(
                section_key="azerbaijan_contribution",
                name="Contribution to Azerbaijan (State Programme)",
                status=SectionStatus.MISSING,
                score=0.0,
                max_score=6.0,
                detected_phrases=[],
                feedback="State Programme reviewers heavily weigh how your degree benefits Azerbaijan's economic diversification.",
            )
        sections.append(sec_aze)
    else:
        # For non-state programme, allocate standard closing synthesis
        sections.append(
            SectionMatch(
                section_key="conclusion",
                name="Concluding Synthesis",
                status=SectionStatus.STRONG if total_sentences >= 15 else SectionStatus.PRESENT,
                score=6.0 if total_sentences >= 15 else 4.0,
                max_score=6.0,
                detected_phrases=["concluding synthesis"],
                feedback="Summary synthesis tying together your preparedness and readiness.",
            )
        )

    sections_score = sum(s.score for s in sections)

    category_scores = {
        "length_hygiene": round(length_score, 1),
        "cliche_originality": round(cliche_score, 1),
        "voice_active_verbs": round(voice_score, 1),
        "readability_metrics": round(metrics_score, 1),
        "narrative_sections": round(sections_score, 1),
    }

    raw_total = length_score + cliche_score + voice_score + metrics_score + sections_score
    overall_score = round(max(0.0, min(100.0, raw_total)), 1)

    if overall_score >= 85.0:
        letter_grade = LetterGrade.A
        verdict = "Rəqabətə Tam Hazır (Outstanding)"
    elif overall_score >= 70.0:
        letter_grade = LetterGrade.B
        verdict = "Güclü Esse, kiçik təkmilləşdirmələr tələb olunur (Strong)"
    elif overall_score >= 50.0:
        letter_grade = LetterGrade.C
        verdict = "Mühüm çatışmazlıqlar mövcuddur (Needs Work)"
    else:
        letter_grade = LetterGrade.D
        verdict = "Əsaslı şəkildə yenidən yazılmalıdır (Major Revision)"

    return SopAnalysisResult(
        overall_score=overall_score,
        letter_grade=letter_grade,
        verdict=verdict,
        word_count=word_count,
        char_count=char_count,
        paragraph_count=paragraph_count,
        average_sentence_length=avg_sentence_len,
        reading_time_minutes=reading_time,
        flesch_reading_ease=flesch_score,
        passive_voice_percentage=passive_pct,
        lexical_diversity=lexical_diversity,
        category_scores=category_scores,
        sections=sections,
        issues=issues,
        strengths=strengths,
    )


def analyze_cv_text(req: CvAnalysisRequest) -> CvAnalysisResult:
    """Analyzes an Academic CV / Resume text for international admissions standards."""
    raw_text = req.text.strip()
    words = re.findall(r"\b[\w'-]+\b", raw_text)
    word_count = len(words)

    # Bullet detection (lines starting with -, *, •, or numbered)
    lines = raw_text.splitlines()
    bullet_lines = [
        line.strip() for line in lines
        if re.match(r"^(\s*[-*•–—]|\s*\d+\.)\s+", line)
    ]
    bullet_count = len(bullet_lines)

    # Detect action verb beginnings in bullets
    action_verb_count = 0
    quantified_count = 0
    for b in bullet_lines:
        clean_b = re.sub(r"^(\s*[-*•–—]|\s*\d+\.)\s+", "", b).strip()
        first_word = clean_b.split()[0].lower() if clean_b.split() else ""
        if first_word in STRONG_ACTION_VERBS:
            action_verb_count += 1
        if re.search(r"\b(\d+(\.\d+)?%|\$\d+|\d+\+?)\b", clean_b):
            quantified_count += 1

    # Standard academic CV sections
    standard_sections = {
        "education": ["education", "academic background", "university", "degree", "bachelor", "master"],
        "experience": ["experience", "employment", "internship", "professional experience", "work history"],
        "research_projects": ["research", "projects", "publications", "thesis", "selected projects"],
        "skills": ["skills", "technical skills", "languages", "competencies", "tools"],
        "honors_awards": ["honors", "awards", "scholarships", "achievements", "certifications"],
    }

    sections_detected: List[str] = []
    missing_sections: List[str] = []
    for sec_name, keywords in standard_sections.items():
        found = any(re.search(r"\b" + kw + r"\b", raw_text, re.IGNORECASE) for kw in keywords)
        if found:
            sections_detected.append(sec_name)
        else:
            missing_sections.append(sec_name)

    issues: List[WritingIssue] = []
    strengths: List[str] = []
    score = 100.0

    # Section completeness
    if len(sections_detected) >= 4:
        strengths.append(f"Comprehensive structure: {len(sections_detected)} standard academic CV sections detected.")
    else:
        deduction = len(missing_sections) * 8.0
        score -= deduction
        issues.append(
            WritingIssue(
                id="missing_cv_sections",
                category="Structure",
                severity=IssueSeverity.WARNING,
                message=f"Missing key sections: {', '.join(missing_sections)}.",
                suggestion="Add dedicated headings for Research, Experience, and Technical Skills.",
            )
        )

    # Bullet audit
    if bullet_count >= 6:
        strengths.append(f"Well-structured itemized bullet points ({bullet_count} bullets).")
        quant_pct = round((quantified_count / max(1, bullet_count)) * 100.0, 1)
        if quant_pct >= 40.0:
            strengths.append(f"High metric quantification ({quant_pct}% of bullets feature numbers or data).")
        else:
            score -= 10.0
            issues.append(
                WritingIssue(
                    id="low_quantification",
                    category="Content",
                    severity=IssueSeverity.SUGGESTION,
                    message=f"Only {quantified_count} of {bullet_count} bullets contain quantified metrics.",
                    suggestion="Add measurable outcomes (e.g. 'reduced latency by 35%', 'processed 50k records').",
                )
            )
    else:
        score -= 15.0
        issues.append(
            WritingIssue(
                id="few_bullets",
                category="Structure",
                severity=IssueSeverity.WARNING,
                message="CV relies too heavily on narrative blocks rather than bulleted impact points.",
                suggestion="Format experience and projects as bullet points beginning with action verbs.",
            )
        )

    # Sensitive personal data audit (US/UK standard)
    if re.search(r"\b(marital status|date of birth|religion|nationality|gender|photo)\b", raw_text, re.IGNORECASE):
        issues.append(
            WritingIssue(
                id="sensitive_info",
                category="Compliance",
                severity=IssueSeverity.WARNING,
                message="Detected personal demographic info (marital status, date of birth, or gender).",
                suggestion="For US and UK university applications, omit personal demographics to comply with anti-bias guidelines.",
            )
        )
        score -= 5.0

    overall_score = round(max(0.0, min(100.0, score)), 1)
    if overall_score >= 85.0:
        letter_grade = LetterGrade.A
        verdict = "Beynəlxalq Standartlara Uyğundur (Strong Academic CV)"
    elif overall_score >= 70.0:
        letter_grade = LetterGrade.B
        verdict = "Yaxşı, format və detal təkmilləşdirmələri lazımdır"
    else:
        letter_grade = LetterGrade.C
        verdict = "Struktur və detal çatışmazlıqları var"

    return CvAnalysisResult(
        overall_score=overall_score,
        letter_grade=letter_grade,
        verdict=verdict,
        word_count=word_count,
        bullet_count=bullet_count,
        quantified_bullets_count=quantified_count,
        action_verb_bullets_count=action_verb_count,
        sections_detected=sections_detected,
        missing_sections=missing_sections,
        issues=issues,
        strengths=strengths,
    )


# Curated Exemplary SOP Templates
CURATED_SOP_TEMPLATES: List[SopTemplate] = [
    SopTemplate(
        id="cs_ai_master",
        title="MSc Computer Science & Artificial Intelligence",
        degree_level="master",
        field="stem",
        description="High-scoring template tailored for competitive European & US graduate programs, featuring undergraduate research and State Programme contribution.",
        word_count=724,
        content="""My undergraduate journey in Computer Engineering at Baku Higher Oil School sparked my commitment to distributed machine learning systems. During my junior year, while engineering an automated telemetry monitoring pipeline for industrial sensor arrays, I confronted firsthand the limitations of centralized inference architectures under volatile network conditions. This experience catalyzed my undergraduate thesis, where I developed an adaptive edge-quantization model that compressed neural network parameters by 42% while retaining 96.8% classification accuracy.

Building upon this foundation, I pursued an internship at SOCAR Digital, where I designed and deployed a fault-tolerant predictive maintenance microservice processing over 50,000 real-time telemetry events per minute. Collaborating with senior systems architects, I formulated an anomaly detection benchmark using streaming autoencoders, reducing unplanned equipment downtime alerts by 28%. While this project confirmed the industrial efficacy of applied machine learning, it also revealed pressing theoretical bottlenecks in model interpretability and decentralized data privacy.

The Master of Science in Computer Science at the Technical University of Munich presents the optimal environment to investigate these challenges. I am particularly eager to join the Machine Learning for Intelligent Systems Laboratory under Professor Matthias Niessner, whose published work on scalable neural rendering and robust representation learning directly mirrors my research trajectory. Furthermore, courses such as Advanced Distributed Systems and Privacy-Preserving Machine Learning will equip me with the formal mathematical rigor required to architect resilient, privacy-preserving computational infrastructures.

Following graduation, my short-term objective is to contribute as a Machine Learning Infrastructure Engineer within an international research group, optimizing large-scale distributed training paradigms. In the long term, under the framework of the Republic of Azerbaijan 2022-2026 State Programme, my goal is to transfer this specialized technical acumen back to Azerbaijan's burgeoning technology ecosystem. By spearheading the development of national AI compute infrastructure and mentoring the next generation of Azerbaijani computer scientists, I aim to directly foster economic diversification away from hydrocarbon dependence toward a high-value knowledge economy. I am prepared to dedicate the full measure of my technical diligence to your esteemed program.""",
    ),
    SopTemplate(
        id="data_science_state_programme",
        title="MSc Data Science & Analytics (State Programme Framework)",
        degree_level="master",
        field="stem",
        description="Comprehensive motivation letter addressing bilateral scholarships, economic diversification in Azerbaijan, and clear faculty alignment.",
        word_count=685,
        content="""The transition toward data-driven governance and renewable energy optimization represents the single most consequential challenge confronting emerging economies today. Having completed my Bachelor of Science in Applied Mathematics at Baku State University with a cumulative GPA of 3.86/4.0, I have systematically cultivated the analytical and statistical foundation necessary to analyze complex stochastic systems. My undergraduate capstone project modeled time-series load forecasting for urban municipal grids, implementing gradient boosting regressors that outperformed classical ARIMA baselines by 18.4% in mean squared error.

Complementing my academic rigor, my tenure as a Junior Data Analyst at the Central Bank of Azerbaijan exposed me to macro-prudential econometrics and big-data streaming pipelines. I formulated automated validation algorithms for liquidity risk reporting, streamlining quarterly stress testing across 23 commercial banking entities and diminishing data reconciliation latency by 35%. This engagement underscored that statistical models are only as potent as their underlying algorithmic integrity and ethical guardrails.

The Master of Science in Data Science at Imperial College London stands out for its interdisciplinary synergy between probabilistic machine learning and high-performance computing. I am especially inspired by the research conducted at the Data Science Institute, where recent publications on spatio-temporal anomaly detection offer profound implications for smart grid management. The opportunity to study modules such as Big Data Computing and Bayesian Deep Learning will bridge the gap between my current empirical modeling capabilities and frontier computational research.

Upon completing my studies, I intend to leverage the 2022-2026 State Programme scholarship to return immediately to Baku. My vision is to spearhead public-sector predictive modeling initiatives within the Ministry of Digital Development and Transport, developing open-source algorithmic platforms that accelerate civic digitization and renewable energy forecasting. Through rigorous foreign study, I am committed to converting advanced data science into sustainable national impact.""",
    ),
    SopTemplate(
        id="chevening_leadership",
        title="Chevening Scholarship Leadership & Networking Essay",
        degree_level="master",
        field="business",
        description="Leadership essay structured around the 2,800-hour work experience gate and post-study 2-year home return commitment.",
        word_count=520,
        content="""Leadership, in my professional experience, is the capacity to mobilize diverse stakeholders around a rigorous quantitative vision while cultivating individual agency. During my tenure as Project Lead at the Azerbaijan FinTech Association, I spearheaded the National Open Banking Harmonization Initiative, a multilateral consortium uniting twelve commercial banking institutions, regulatory compliance officers, and agile software startups.

When divergent regulatory interpretations threatened to stall consensus, I initiated bi-weekly technical working groups, disaggregating the 200-page API mandate into four modular pilot sprints. By establishing an objective sandbox testing environment, I facilitated collaborative debugging between competing institutions, culminating in the successful launch of Azerbaijan's first interoperable payment gateway four weeks ahead of schedule.

Through this initiative, I accrued over 3,200 verified hours of project management and regulatory advisory experience. However, expanding inclusive financial infrastructure requires more than domestic operational agility; it demands deep immersion in the UK's global financial regulatory architecture. Pursuing the MSc in Financial Technology and Regulation in the United Kingdom through the Chevening Scholarship will provide direct access to global fintech leaders and policy innovators.

Upon completion of my degree, I will return to Azerbaijan for the required two-year period, channeling my UK network and regulatory insights directly into modernizing the nation's digital micro-lending framework for small enterprises and rural agricultural communities.""",
    ),
];
