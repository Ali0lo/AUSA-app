import pytest
from langchain_core.messages import HumanMessage
from app.services.agent.graph import application_agent
from app.services.agent.state import AgentState
from app.services.agent.tools import (
    STUDENT_PROFILE_STORE,
    check_missing_documents,
    draft_motivation_letter,
    extract_and_update_profile,
    get_program_deadline,
)


def test_agent_state_schema():
    state: AgentState = {
        "messages": [HumanMessage(content="Hello")],
        "student_id": "std_123",
        "target_program_id": "prog_456",
        "missing_documents": ["transcript"],
        "application_stage": "gathering_info"
    }
    assert state["student_id"] == "std_123"
    assert state["target_program_id"] == "prog_456"
    assert state["application_stage"] == "gathering_info"
    assert len(state["missing_documents"]) == 1


def test_tools_execution():
    missing_docs = check_missing_documents.invoke({"student_id": "std_1", "program_id": "prog_1"})
    assert isinstance(missing_docs, list)
    assert "official_transcript" in missing_docs

    # There is no wired-in source of verified per-programme deadlines, so the tool must
    # say so honestly rather than invent a date. This previously asserted the fabricated
    # "November 30, 2026" -- the fabrication this test now guards against.
    deadline = get_program_deadline.invoke({"program_id": "prog_1"})
    assert "November 30, 2026" not in deadline
    assert "prog_1" in deadline
    assert "do not have a verified application deadline" in deadline

    letter = draft_motivation_letter.invoke({"student_id": "std_1", "program_id": "prog_1"})
    assert "Dear Admissions Committee" in letter
    assert "std_1" in letter


def test_extract_and_update_profile_preserves_existing_degree_level():
    """A document that says nothing about degree level must not relabel the student.

    This previously defaulted degree_level to "master" unconditionally on every call --
    a bachelor applicant who uploaded a transcript with only a GPA on it would be
    silently relabelled a master's applicant, and matching/engine.py's hard degree-level
    filter would then report every bachelor programme as a 0% match.
    """
    student_id = "std_test_degree_preserve"
    STUDENT_PROFILE_STORE[student_id] = {"degree_level": "bachelor"}

    extract_and_update_profile.invoke({
        "document_text": "Transcript. GPA: 3.20 / 4.0.",
        "student_id": student_id,
    })

    assert STUDENT_PROFILE_STORE[student_id]["degree_level"] == "bachelor"


def test_extract_and_update_profile_leaves_unknown_degree_unknown():
    """A student with no prior degree_level and a document that doesn't state one
    must end up with degree_level still unknown, not a default of "master"."""
    student_id = "std_test_degree_unknown"
    STUDENT_PROFILE_STORE.pop(student_id, None)

    extract_and_update_profile.invoke({
        "document_text": "Transcript. GPA: 3.20 / 4.0.",
        "student_id": student_id,
    })

    assert STUDENT_PROFILE_STORE[student_id].get("degree_level") is None


@pytest.mark.asyncio
async def test_application_agent_invocation():
    initial_state: AgentState = {
        "messages": [HumanMessage(content="What documents am I missing for program prog_100?")],
        "student_id": "std_007",
        "target_program_id": "prog_100",
        "missing_documents": [],
        "application_stage": "gathering_info"
    }
    
    output_state = await application_agent.ainvoke(initial_state)
    assert "messages" in output_state
    assert len(output_state["messages"]) >= 2
    last_msg = output_state["messages"][-1]
    assert last_msg.content != ""
