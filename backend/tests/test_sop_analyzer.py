"""Comprehensive unit and integration tests for the SOP & Academic CV rubric analysis engine.
"""

from fastapi.testclient import TestClient
import pytest

from app.domain.sop_analyzer import (
    CURATED_SOP_TEMPLATES,
    CvAnalysisRequest,
    IssueSeverity,
    LetterGrade,
    SectionStatus,
    SopAnalysisRequest,
    analyze_cv_text,
    analyze_sop_text,
    calculate_flesch_reading_ease,
)
from app.main import app

client = TestClient(app)


class TestSopDomainLogic:
    """Unit tests for SOP evaluation heuristics and scoring."""

    def test_cliche_childhood_opening(self):
        text = "Ever since I was a child, I wanted to build software. Now I am applying for MSc."
        req = SopAnalysisRequest(text=text, word_limit_min=10)
        res = analyze_sop_text(req)
        cliche_issues = [i for i in res.issues if i.category == "Cliche"]
        assert len(cliche_issues) > 0
        assert any("Childhood" in i.message for i in cliche_issues)

    def test_cliche_passion_and_dictionary(self):
        text = (
            "Webster's dictionary defines technology as applied science. "
            "I have always been passionate about artificial intelligence. "
            "Allow me to introduce myself, I am a hardworking and motivated individual."
        )
        req = SopAnalysisRequest(text=text, word_limit_min=10)
        res = analyze_sop_text(req)
        cliche_messages = [i.message for i in res.issues if i.category == "Cliche"]
        assert any("Dictionary" in m for m in cliche_messages)
        assert any("Passion" in m for m in cliche_messages)
        assert any("Conversational" in m or "Resume Buzzword" in m for m in cliche_messages)

    def test_word_count_deficit(self):
        short_text = "This is a brief paragraph that is way too short to serve as an academic statement."
        req = SopAnalysisRequest(text=short_text, word_limit_min=500)
        res = analyze_sop_text(req)
        length_issues = [i for i in res.issues if i.id == "length_under"]
        assert len(length_issues) == 1
        assert res.category_scores["length_hygiene"] < 15.0

    def test_word_count_excess(self):
        # Generate 600 words when max is 500
        words = ["research", "academic", "algorithm", "data", "engineering", "system"] * 105
        long_text = " ".join(words)
        req = SopAnalysisRequest(text=long_text, word_limit_max=500)
        res = analyze_sop_text(req)
        excess_issues = [i for i in res.issues if i.id == "length_over"]
        assert len(excess_issues) == 1

    def test_few_paragraphs_warning(self):
        # Single continuous block with no double newline
        words = ["Machine learning transforms computational biology.", "Data pipelines process genomes."] * 50
        block_text = " ".join(words)
        req = SopAnalysisRequest(text=block_text, word_limit_min=50)
        res = analyze_sop_text(req)
        assert res.paragraph_count == 1
        para_issues = [i for i in res.issues if i.id == "paragraphs_few"]
        assert len(para_issues) == 1

    def test_passive_voice_intensity(self):
        passive_text = (
            "The experiment was conducted by our team. "
            "The data were analyzed using statistical models. "
            "A novel algorithm was engineered and tests were performed. "
            "Great results were obtained."
        )
        req = SopAnalysisRequest(text=passive_text, word_limit_min=10)
        res = analyze_sop_text(req)
        assert res.passive_voice_percentage > 30.0
        assert any(i.id == "voice_passive_high" for i in res.issues)

    def test_action_verbs_presence(self):
        active_text = (
            "During my thesis, I spearheaded the development of edge models. "
            "I engineered distributed pipelines and optimized parameter convergence. "
            "Furthermore, I synthesized multi-sensor data, modeled latency patterns, "
            "and deployed microservices processing 50,000 telemetry packets per second."
        )
        req = SopAnalysisRequest(text=active_text, word_limit_min=10)
        res = analyze_sop_text(req)
        assert any("action verb presence" in s.lower() for s in res.strengths)

    def test_sections_detection_strong(self):
        full_sample = CURATED_SOP_TEMPLATES[0].content
        req = SopAnalysisRequest(text=full_sample, is_state_programme=True)
        res = analyze_sop_text(req)

        section_keys = {s.section_key: s for s in res.sections}
        assert "hook" in section_keys
        assert "academic" in section_keys
        assert "university" in section_keys
        assert "career" in section_keys
        assert "azerbaijan_contribution" in section_keys

        assert section_keys["academic"].status == SectionStatus.STRONG
        assert section_keys["university"].status == SectionStatus.STRONG
        assert section_keys["azerbaijan_contribution"].status == SectionStatus.STRONG

    def test_sections_missing_state_programme(self):
        text_no_aze = (
            "My research curiosity is sparked by quantum computing. "
            "During my bachelor study, my thesis investigated topological qubits. "
            "The curriculum at Oxford University offers advanced modules under Professor Smith. "
            "My long-term career goal is to work as a staff scientist."
        )
        req = SopAnalysisRequest(text=text_no_aze, is_state_programme=True, word_limit_min=10)
        res = analyze_sop_text(req)
        aze_sec = next(s for s in res.sections if s.section_key == "azerbaijan_contribution")
        assert aze_sec.status == SectionStatus.MISSING
        assert aze_sec.score == 0.0

    def test_curated_templates_high_grade(self):
        for tpl in CURATED_SOP_TEMPLATES:
            min_w = 200 if tpl.word_count < 300 else 250
            res = analyze_sop_text(SopAnalysisRequest(text=tpl.content, word_limit_min=min_w))
            assert res.overall_score >= 70.0
            assert res.letter_grade in (LetterGrade.A, LetterGrade.B)

    def test_flesch_reading_ease_metric(self):
        prose = "The rapid proliferation of distributed streaming systems presents significant concurrency challenges."
        score = calculate_flesch_reading_ease(prose)
        assert 0.0 <= score <= 100.0


class TestCvDomainLogic:
    """Unit tests for Academic CV / Resume auditing."""

    def test_cv_section_detection(self):
        cv = """
        John Doe | john@example.com
        Education
        BSc Computer Science, 2024
        Professional Experience
        Software Engineer Intern at TechCorp
        Research and Projects
        Built distributed key-value store in Rust
        Technical Skills
        Python, C++, Docker, Kubernetes
        Honors and Awards
        National Olympiad in Informatics, 2nd place
        """
        res = analyze_cv_text(CvAnalysisRequest(text=cv))
        assert len(res.sections_detected) == 5
        assert len(res.missing_sections) == 0

    def test_cv_bullet_points_and_quantification(self):
        cv = """
        Education
        BSc Engineering
        Experience
        - Spearheaded telemetry microservices processing 50,000 events/min
        - Engineered automated data validation algorithms reducing latency by 35%
        - Designed distributed training pipelines optimizing GPU utilization by 22%
        - Streamlined continuous deployment cycles by 40% across 5 services
        - Automated regression testing suites increasing code coverage to 92%
        - Formulated load balancing heuristics handling 100,000 concurrent sockets
        Skills
        Python, Go, Docker
        """
        res = analyze_cv_text(CvAnalysisRequest(text=cv))
        assert res.bullet_count == 6
        assert res.quantified_bullets_count == 6
        assert res.action_verb_bullets_count == 6
        assert res.overall_score >= 80.0

    def test_cv_sensitive_data_warning(self):
        cv = """
        Date of Birth: 15/05/2001
        Marital Status: Single
        Education: BSc Engineering
        """
        res = analyze_cv_text(CvAnalysisRequest(text=cv))
        assert any(i.id == "sensitive_info" for i in res.issues)


class TestSopApiEndpoints:
    """Integration tests for FastAPI /api/v1/sop router."""

    def test_api_templates(self):
        resp = client.get("/api/v1/sop/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3
        assert "title" in data[0]
        assert "content" in data[0]

    def test_api_cliches(self):
        resp = client.get("/api/v1/sop/cliches")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 10
        assert "pattern" in data[0]
        assert "recommendation" in data[0]

    def test_api_analyze_sop(self):
        sample = CURATED_SOP_TEMPLATES[0].content
        resp = client.post("/api/v1/sop/analyze", json={"text": sample, "is_state_programme": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_score"] > 80.0
        assert data["letter_grade"] in ["A", "B"]
        assert len(data["sections"]) == 5
        assert "category_scores" in data

    def test_api_analyze_cv(self):
        cv_text = """
        Education
        - BSc in Computer Science, 2024
        Experience
        - Engineered cloud microservice reducing latency by 40%
        - Spearheaded database indexing for 10M rows
        Skills
        - Python, Go
        """
        resp = client.post("/api/v1/sop/analyze-cv", json={"text": cv_text})
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "bullet_count" in data
