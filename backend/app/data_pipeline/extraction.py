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
    min_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Minimum required IELTS score")
    min_toefl: Optional[int] = Field(None, ge=0, le=120, description="Minimum required TOEFL score")
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
        tuition_match = re.search(r"(?:tuition|fee)[^\d]*\$?\s*([\d,]+)", text, re.IGNORECASE)
        
        found_count = sum(1 for m in [gpa_match, ielts_match, toefl_match, tuition_match] if m)
        calc_confidence = round(min(100.0, (found_count / 4.0) * 100.0), 1) if found_count > 0 else 30.0

        min_gpa = float(gpa_match.group(1)) if gpa_match else None
        min_ielts = float(ielts_match.group(1)) if ielts_match else None
        min_toefl = int(toefl_match.group(1)) if toefl_match else None
        tuition_fee = float(tuition_match.group(1).replace(",", "")) if tuition_match else None

        degree_level: Optional[DegreeLevel] = None
        if "master" in text.lower() or "m.sc" in text.lower():
            degree_level = "master"
        elif "bachelor" in text.lower() or "b.sc" in text.lower():
            degree_level = "bachelor"
        elif "phd" in text.lower() or "doctorate" in text.lower():
            degree_level = "phd"

        return ExtractedProgramData(
            university_name="Extracted University" if "university" in text.lower() else None,
            program_name="Extracted Program",
            degree_level=degree_level,
            min_gpa=min_gpa,
            min_ielts=min_ielts,
            min_toefl=min_toefl,
            tuition_fee_usd=tuition_fee,
            confidence_score=calc_confidence,
            extraction_notes="Extracted via fallback parser."
        )
