from typing import Literal, Optional
from pydantic import BaseModel, Field


DegreeLevel = Literal["bachelor", "master", "phd"]


class ExtractionUnavailableError(RuntimeError):
    """Raised when extraction cannot run. Never return heuristically-invented fields.

    The caller decides what to do with a page it could not read. What it must not do is
    receive a plausible-looking record that nobody extracted -- see the note above the
    fallback that used to live in extract_program_info_from_text.
    """


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
    # No default. The blocked-account minimum is set annually by the Auswärtiges Amt, so a
    # constant baked in here would be quietly stale AND would be indistinguishable from a
    # figure actually read off the page. Absent means absent.
    blocked_account_eur: Optional[float] = Field(None, description="Blocked bank account financial minimum in EUR for German visa, as stated by the source")

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

    # A regex fallback stood here until 2026-08-31. When the LLM call raised for ANY reason
    # -- missing OPENAI_API_KEY, network failure, rate limit, malformed response, import
    # error -- a bare `except Exception` silently substituted a heuristic parser that then
    # invented the record: university_name="Extracted University" and
    # program_name="Extracted Program" written as literal values, blocked_account_eur
    # hardcoded to 11208.0, requires_studienkolleg set by mere substring presence, and
    # country inferred from "baku" appearing anywhere in the page.
    #
    # Worst of all it fabricated the confidence score that the human review queue gates on:
    # (found_count / 3.0) * 100, so three regex hits produced a confidence of 100.0 -- a
    # perfect score from a parser that had just invented the university name -- which cleared
    # the 85% threshold and published without any human ever seeing it. And in CI, where no
    # API key exists, the try block ALWAYS raised, so the pipeline tests were green on the
    # fabricated path rather than on extraction.
    #
    # ADR-0004 forbids exactly this. A page we could not read yields no record.
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT_TEMPLATE)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        structured_llm = llm.with_structured_output(ExtractedProgramData)

        chain = prompt | structured_llm
        result: ExtractedProgramData = await chain.ainvoke({"text": text})
        return result
    except Exception as exc:
        raise ExtractionUnavailableError(
            f"Extraction failed and no substitute is produced: {exc}"
        ) from exc
