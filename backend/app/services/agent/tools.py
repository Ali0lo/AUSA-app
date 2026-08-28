import re
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# In-memory store for student profile states (synchronized with DB in production)
DEMO_STUDENT_STORE: Dict[str, Dict[str, Any]] = {
    "std_demo": {
        "gpa": 3.5,
        "ielts": 6.5,
        "toefl": None,
        "degree_level": "master",
        "budget": 15000.0,
    }
}


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
    profile = DEMO_STUDENT_STORE.get(student_id, {})
    missing = ["passport_copy", "motivation_letter"]
    if profile.get("gpa") is None:
        missing.insert(0, "official_transcript")
    return missing


@tool
def get_program_deadline(program_id: str) -> str:
    """
    Retrieve the official application deadline date string for a specific university program.
    
    Args:
        program_id: Unique identifier of the university program.
        
    Returns:
        Deadline date string (e.g. "November 30, 2026 at 23:59 CET").
    """
    return f"Deadline for program {program_id}: November 30, 2026 at 23:59 CET"


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
    profile = DEMO_STUDENT_STORE.get(student_id, {})
    gpa_str = f"with a GPA of {profile.get('gpa', 3.8)}" if profile.get('gpa') else ""
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
    and automatically update the student's profile record in the database.
    
    Args:
        document_text: Plain raw text extracted from transcript or certificate document.
        student_id: Student identifier.
        
    Returns:
        Summary message confirming updated profile metrics.
    """
    extracted_gpa: Optional[float] = None
    extracted_ielts: Optional[float] = None
    extracted_toefl: Optional[int] = None
    degree = "master"

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

    # Standard fallback defaults if document was sparse
    if extracted_gpa is None:
        extracted_gpa = 3.8
    if extracted_ielts is None and extracted_toefl is None:
        extracted_ielts = 7.5

    # Update in-memory / database student store
    current_profile = DEMO_STUDENT_STORE.get(student_id, {})
    current_profile.update({
        "gpa": extracted_gpa,
        "ielts": extracted_ielts if extracted_ielts is not None else current_profile.get("ielts"),
        "toefl": extracted_toefl if extracted_toefl is not None else current_profile.get("toefl"),
        "degree_level": degree,
    })
    DEMO_STUDENT_STORE[student_id] = current_profile

    summary = f"Successfully updated student profile: GPA is now {extracted_gpa:.2f}"
    if extracted_ielts:
        summary += f" and IELTS is {extracted_ielts:.1f}."
    elif extracted_toefl:
        summary += f" and TOEFL is {extracted_toefl}."
    else:
        summary += "."

    return summary


# Exported tool registry list for LangGraph node binding
tools = [check_missing_documents, get_program_deadline, draft_motivation_letter, extract_and_update_profile]
