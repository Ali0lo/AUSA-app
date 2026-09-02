import re
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# In-memory store for student profile states within an agent session. This is NOT the
# database -- extract_and_update_profile writes here, and the students table is never
# touched by any chat or upload path (README corrected accordingly). It starts empty:
# a student who has not uploaded a document or told the agent their scores has no
# profile here, not an invented one. Previously seeded with a fabricated "std_demo"
# profile (gpa 3.5, ielts 6.5, degree_level "master"), so calling /chat/agent/state
# with no arguments returned invented data as fact (ADR-0004).
STUDENT_PROFILE_STORE: Dict[str, Dict[str, Any]] = {}


class ProfileExtractionResult(BaseModel):
    """Structured extraction schema for academic document parsing."""
    extracted_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Extracted GPA on a 4.0 scale")
    extracted_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Extracted IELTS overall band score")
    extracted_toefl: Optional[int] = Field(None, ge=0, le=120, description="Extracted TOEFL iBT score")
    degree_level: Optional[str] = Field(None, description="Extracted degree level (bachelor, master, phd)")


@tool
def check_missing_documents(student_id: str, program_id: str) -> List[str]:
    """
    Check and return the list of missing application documents for a given student and target program.
    
    Args:
        student_id: Unique identifier of the student.
        program_id: Unique identifier of the university program.
        
    Returns:
        List of missing document names (e.g. ["transcript", "passport", "motivation_letter"]).
    """
    profile = STUDENT_PROFILE_STORE.get(student_id, {})
    missing = ["passport_copy", "motivation_letter"]
    if profile.get("gpa") is None:
        missing.insert(0, "official_transcript")
    return missing


@tool
def get_program_deadline(program_id: str) -> str:
    """
    Report whether a verified application deadline is known for a specific university program.

    This assistant has no source of verified per-programme deadlines wired in yet, so it
    never invents one -- a confidently wrong deadline is the most damaging thing an
    application advisor can say (ADR-0004). Previously this returned the same hardcoded
    "November 30, 2026" for every program_id, real or not.

    Args:
        program_id: Unique identifier of the university program.

    Returns:
        A string stating that no verified deadline is available, and directing the
        student to the official source.
    """
    return (
        f"I do not have a verified application deadline for program {program_id}. "
        "Please check the official university admissions page for the exact date, "
        "or add it to your application tracker once you find it."
    )


@tool
def draft_motivation_letter(student_id: str, program_id: str) -> str:
    """
    Generate a customized motivation letter draft template based on student and program details.
    
    Args:
        student_id: Unique identifier of the student.
        program_id: Unique identifier of the university program.
        
    Returns:
        Structured motivation letter text template.
    """
    profile = STUDENT_PROFILE_STORE.get(student_id, {})
    gpa_str = f"with a GPA of {profile.get('gpa')}" if profile.get("gpa") else ""
    return (
        f"Dear Admissions Committee,\n\n"
        f"I am writing to express my strong interest in enrolling in program {program_id}. "
        f"As student {student_id} {gpa_str}, my academic background and long-term career aspirations "
        f"align strongly with the academic rigors of this program.\n\n"
        f"Sincerely,\nStudent {student_id}"
    )


@tool
def extract_and_update_profile(document_text: str, student_id: str = "std_demo") -> str:
    """
    Extract structured academic metrics (GPA, IELTS/TOEFL scores, degree level) from uploaded document text
    and update the student's in-session profile record (STUDENT_PROFILE_STORE). This is not
    a database write -- the profile does not persist past this process's lifetime.
    
    Args:
        document_text: Plain raw text extracted from transcript or certificate document.
        student_id: Student identifier.
        
    Returns:
        Summary message confirming updated profile metrics.
    """
    extracted_gpa: Optional[float] = None
    extracted_ielts: Optional[float] = None
    extracted_toefl: Optional[int] = None
    # Absent, not "master" -- degree level is a hard eligibility filter downstream
    # (matching/engine.py). A document that does not state a degree level must leave
    # the existing value alone, exactly like the other three fields below.
    degree: Optional[str] = None

    # 1. Structured LLM extraction attempt
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_template(
            "Extract GPA (4.0 scale), IELTS (0-9), TOEFL (0-120), and degree_level from this academic document text:\n---\n{text}\n---"
        )
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        structured_llm = llm.with_structured_output(ProfileExtractionResult)

        chain = prompt | structured_llm
        res: ProfileExtractionResult = chain.invoke({"text": document_text})
        extracted_gpa = res.extracted_gpa
        extracted_ielts = res.extracted_ielts
        extracted_toefl = res.extracted_toefl
        if res.degree_level:
            degree = res.degree_level.lower()
    except Exception:
        pass

    # 2. Heuristic fallback parsing if LLM is unavailable or offline
    if extracted_gpa is None:
        gpa_match = re.search(r"gpa[^\d]*(\d\.\d+)", document_text, re.IGNORECASE)
        if gpa_match:
            extracted_gpa = float(gpa_match.group(1))

    if extracted_ielts is None:
        ielts_match = re.search(r"ielts[^\d]*(\d\.\d+)", document_text, re.IGNORECASE)
        if ielts_match:
            extracted_ielts = float(ielts_match.group(1))

    if extracted_toefl is None:
        toefl_match = re.search(r"toefl[^\d]*(\d+)", document_text, re.IGNORECASE)
        if toefl_match:
            extracted_toefl = int(toefl_match.group(1))

    # A document that yields nothing updates nothing. This previously defaulted to
    # GPA 3.8 / IELTS 7.5 and reported them as "successfully updated" -- inventing the
    # student's own qualifications, which then drive every eligibility check made for
    # them. An unreadable transcript is a fact to report, not a gap to fill (ADR-0004).
    if extracted_gpa is None and extracted_ielts is None and extracted_toefl is None and degree is None:
        return (
            "No academic metrics could be read from this document. Nothing was changed on "
            "the profile. Please check the file is a readable transcript or certificate, "
            "or enter the scores manually."
        )

    # Update in-memory / database student store. Fields the document did not mention keep
    # whatever the profile already held -- absent is not the same as zero, and that now
    # includes degree_level: a document that says nothing about degree level must not
    # relabel the student's existing degree level (or invent one where none was held).
    current_profile = STUDENT_PROFILE_STORE.get(student_id, {})
    current_profile.update({
        "gpa": extracted_gpa if extracted_gpa is not None else current_profile.get("gpa"),
        "ielts": extracted_ielts if extracted_ielts is not None else current_profile.get("ielts"),
        "toefl": extracted_toefl if extracted_toefl is not None else current_profile.get("toefl"),
        "degree_level": degree if degree is not None else current_profile.get("degree_level"),
    })
    STUDENT_PROFILE_STORE[student_id] = current_profile

    found = []
    if extracted_gpa is not None:
        found.append(f"GPA {extracted_gpa:.2f}")
    if extracted_ielts is not None:
        found.append(f"IELTS {extracted_ielts:.1f}")
    if extracted_toefl is not None:
        found.append(f"TOEFL {extracted_toefl}")
    if degree is not None:
        found.append(f"Degree level {degree}")

    return f"Updated student profile from the document: {', '.join(found)}."


# Exported tool registry list for LangGraph node binding
tools = [check_missing_documents, get_program_deadline, draft_motivation_letter, extract_and_update_profile]
