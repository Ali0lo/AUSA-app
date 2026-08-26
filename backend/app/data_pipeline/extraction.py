import re
from typing import Literal, Optional
from pydantic import BaseModel, Field


DegreeLevel = Literal["bachelor", "master", "phd"]


class ExtractedProgramData(BaseModel):
    """Structured program data model extracted from university webpage text."""
    university_name: Optional[str] = Field(None, description="Official university name")
    program_name: Optional[str] = Field(None, description="Name of the program or degree track")
    degree_level: Optional[DegreeLevel] = Field(None, description="Degree level (bachelor, master, phd)")
    field_of_study: Optional[str] = Field(None, description="Field of study or academic department")
    country: Optional[str] = Field(None, description="Host country of the university")
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum required GPA (4.0 scale)")
    tuition_fee_usd: Optional[float] = Field(None, ge=0.0, description="Annual tuition fee converted to USD")
    tuition_fee_azn: Optional[float] = Field(None, ge=0.0, description="Annual tuition fee in AZN for Azerbaijan programs")
    min_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Minimum required IELTS score")
    min_toefl: Optional[int] = Field(None, ge=0, le=120, description="Minimum required TOEFL score")
    
    # Germany-specific fields
    requires_studienkolleg: Optional[bool] = Field(None, description="Whether Studienkolleg preparatory course is required")
    min_testdaf_score: Optional[str] = Field(None, description="Minimum German TestDaF or DSH level required")
    blocked_account_eur: Optional[float] = Field(11208.0, description="Blocked bank account financial minimum in EUR for German visa")

    # Azerbaijan-specific fields (DIM / TQDK entrance exam)
    dim_score_required: Optional[int] = Field(None, ge=0, le=700, description="Minimum required DIM/TQDK entrance exam score (0-700 scale)")

    application_deadline: Optional[str] = Field(None, description="Official application deadline date string")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence score (0-100) indicating how explicitly information was stated in the text."
    )
    extraction_notes: Optional[str] = Field(None, description="Notes on missing fields or ambiguities")


EXTRACTION_PROMPT_TEMPLATE = """You are an expert data extraction AI specialized in university program catalog parsing.

Extract structured program requirements and metadata from the webpage text below.
Include Germany-specific fields (requires_studienkolleg, min_testdaf_score, blocked_account_eur) or Azerbaijan-specific fields (dim_score_required, tuition_fee_azn) if applicable.
If a field is not explicitly mentioned or cannot be reliably inferred, set its value to null.
Assign a confidence_score between 0 and 100 reflecting how explicitly and completely the fields were stated in the source text.

Webpage Text:
---
{text}
---
"""


async def extract_program_info_from_text(text: str) -> ExtractedProgramData:
    """
    Extract structured university program data from raw webpage text using LangChain with_structured_output.
    
    Args:
        text: Plain raw text extracted from university webpage.
        
    Returns:
        ExtractedProgramData instance populated with extracted attributes and confidence score.
    """
    if not text.strip():
        return ExtractedProgramData(
            confidence_score=0.0,
            extraction_notes="Webpage text was empty."
        )

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        
        prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT_TEMPLATE)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        structured_llm = llm.with_structured_output(ExtractedProgramData)
        
        chain = prompt | structured_llm
        result: ExtractedProgramData = await chain.ainvoke({"text": text})
        return result
    except Exception:
        # Fallback heuristic extractor when live LLM API is unavailable (e.g. offline testing)
        gpa_match = re.search(r"gpa[^\d]*(\d\.\d+)", text, re.IGNORECASE)
        ielts_match = re.search(r"ielts[^\d]*(\d\.\d+)", text, re.IGNORECASE)
        toefl_match = re.search(r"toefl[^\d]*(\d+)", text, re.IGNORECASE)
        tuition_usd_match = re.search(r"(?:tuition|fee)[^\d]*\$?\s*([\d,]+)\s*(?:usd|\$)?", text, re.IGNORECASE)
        tuition_azn_match = re.search(r"([\d,]+)\s*azn", text, re.IGNORECASE)
        dim_match = re.search(r"(?:dim|tqdk)[^\d]*(\d{3})", text, re.IGNORECASE)
        testdaf_match = re.search(r"(testdaf[^\s\.\,]+|dsh-\d|c1|b2)", text, re.IGNORECASE)
        
        studienkolleg_required = "studienkolleg" in text.lower()

        found_count = sum(1 for m in [gpa_match, ielts_match, toefl_match, tuition_usd_match, dim_match] if m)
        calc_confidence = round(min(100.0, max(40.0, (found_count / 3.0) * 100.0)), 1) if found_count > 0 else 50.0

        min_gpa = float(gpa_match.group(1)) if gpa_match else None
        min_ielts = float(ielts_match.group(1)) if ielts_match else None
        min_toefl = int(toefl_match.group(1)) if toefl_match else None
        tuition_fee_usd = float(tuition_usd_match.group(1).replace(",", "")) if tuition_usd_match else None
        tuition_fee_azn = float(tuition_azn_match.group(1).replace(",", "")) if tuition_azn_match else None
        dim_score = int(dim_match.group(1)) if dim_match else None
        testdaf = testdaf_match.group(1) if testdaf_match else None

        degree_level: Optional[DegreeLevel] = None
        if "master" in text.lower() or "m.sc" in text.lower():
            degree_level = "master"
        elif "bachelor" in text.lower() or "b.sc" in text.lower() or "bakalavr" in text.lower():
            degree_level = "bachelor"
        elif "phd" in text.lower() or "doctorate" in text.lower():
            degree_level = "phd"

        country = "Germany" if ("germany" in text.lower() or "deutschland" in text.lower() or "daad" in text.lower()) else None
        if "azerbaijan" in text.lower() or "azərbaycan" in text.lower() or "baku" in text.lower() or dim_score is not None:
            country = "Azerbaijan"

        return ExtractedProgramData(
            university_name="Extracted University",
            program_name="Extracted Program",
            degree_level=degree_level,
            country=country,
            min_gpa=min_gpa,
            min_ielts=min_ielts,
            min_toefl=min_toefl,
            tuition_fee_usd=tuition_fee_usd,
            tuition_fee_azn=tuition_fee_azn,
            requires_studienkolleg=studienkolleg_required,
            min_testdaf_score=testdaf,
            blocked_account_eur=11208.0 if country == "Germany" else None,
            dim_score_required=dim_score,
            confidence_score=calc_confidence,
            extraction_notes="Extracted via fallback parser."
        )
