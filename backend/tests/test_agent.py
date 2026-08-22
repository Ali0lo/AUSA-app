import pytest
from langchain_core.messages import HumanMessage
from app.services.agent.graph import application_agent
from app.services.agent.state import AgentState
from app.services.agent.tools import (
    check_missing_documents,
    draft_motivation_letter,
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

    deadline = get_program_deadline.invoke({"program_id": "prog_1"})
    assert "November 30, 2026" in deadline

    letter = draft_motivation_letter.invoke({"student_id": "std_1", "program_id": "prog_1"})
    assert "Dear Admissions Committee" in letter
    assert "std_1" in letter


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
