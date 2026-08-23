from typing import List
from langchain_core.tools import tool


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
    # Mock data for demonstration - will connect to database in production
    return ["official_transcript", "passport_copy", "motivation_letter"]


@tool
def get_program_deadline(program_id: str) -> str:
    """
    Retrieve the official application deadline date string for a specific university program.
    
    Args:
        program_id: Unique identifier of the university program.
        
    Returns:
        Deadline date string (e.g. "November 30, 2026 at 23:59 CET").
    """
    # Mock data for demonstration - will connect to database in production
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
    return (
        f"Dear Admissions Committee,\n\n"
        f"I am writing to express my strong interest in enrolling in program {program_id}. "
        f"As student {student_id}, my academic background and long-term career aspirations "
        f"align strong with the academic rigors of this program.\n\n"
        f"Sincerely,\nStudent {student_id}"
    )


# Exported tool registry list for LangGraph node binding
tools = [check_missing_documents, get_program_deadline, draft_motivation_letter]
