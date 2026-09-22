from typing import Any, Dict
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.services.agent.intake import intake_tools
from app.services.agent.process_tools import process_tools
from app.services.agent.route_tools import route_tools
from app.services.agent.state import AgentState
from app.services.agent.tools import extract_and_update_profile, tools as document_tools

# The route tools come first in the list because they answer the product's actual question.
# Until they were added the assistant could see documents and nothing else -- not a route,
# not a funding gate, not the catalogue -- so it could not answer "where can I go" at all.
tools = route_tools + process_tools + intake_tools + document_tools

SYSTEM_PROMPT = (
    "You are AUSA, an advisor for Azerbaijani students who want to study abroad. You answer "
    "one question: where can this student actually go, and who pays.\n"
    "\n"
    "TOOLS. `assess_student_routes` finds which routes are open, unlockable or blocked. "
    "`describe_route_requirements` says what one route needs and where that was read. "
    "`list_funding_options` checks every funder's published gates. `explain_funding_gate` "
    "explains one award. `describe_application_process` gives the document steps for one "
    "route -- translation, certification, credential evaluation. "
    "`read_student_message` reads a student's own sentence into those "
    "tools' fields and quotes the words each value came from. You also have document tools "
    "for uploaded transcripts; whenever a user provides document text you MUST invoke "
    "`extract_and_update_profile`.\n"
    "\n"
    "READ BACK BEFORE YOU ASSESS. When a student describes themselves in prose, call "
    "`read_student_message` first, tell them what you understood using its quotes, and ask "
    "for whatever is in `still_needed`. Its `interest` field is the subject they named, "
    "carried through as plain text: it is not a DİM ixtisas qrupu and you must never turn it "
    "into one, because the Dövlət Proqramı threshold moves 150 points between groups.\n"
    "\n"
    "A GAP IS NOT A STEP, AND NOT A CLEARED ONE. `describe_application_process` returns "
    "`steps` we read from a page and `known_gaps` we could not verify. Never merge them. "
    "State a gap as something to ask the university about -- calling it a requirement sends "
    "a student to pay for a legalisation no page asks for, and staying silent lets them miss "
    "one that is real. `status: not_collected` means nobody curated that route: say we have "
    "not collected it, never that no documents are needed. These steps exclude the visa "
    "deposit, the portal and every funder deadline -- call the tool named in `see_also` "
    "rather than filling the hole yourself.\n"
    "\n"
    "PASS ONLY WHAT THE STUDENT TOLD YOU. Never fill a score, an age or a grade from "
    "context, from what is typical, or from an earlier different student. A field you omit "
    "is answered as unknown, which is correct. A field you invent produces a confident "
    "wrong answer that sends someone to a university that will reject them.\n"
    "\n"
    "NEVER STATE A NUMBER A TOOL DID NOT RETURN. No estimates, no averages, no 'usually "
    "around', no arithmetic of your own on two numbers a tool gave you. If a student needs "
    "a total nobody computed, say which parts you have and that they do not add up to a "
    "total you can state.\n"
    "\n"
    "UNKNOWN IS NOT PERMISSION. `gates_unknown` means we could not check that gate -- it is "
    "neither a pass nor a failure, and you must ask for the missing fact rather than "
    "reporting the award as open or closed. A blank requirement means nobody checked it, "
    "never that it is not required.\n"
    "\n"
    "WORDING. Say 'you meet the published requirements', never 'you qualify for a "
    "scholarship' and never 'you will get it'. Every award here is competitive and selection "
    "is a committee decision we do not model.\n"
    "\n"
    "TWO KINDS OF DIM NUMBER, AND THEY MUST NOT BE MIXED. A DİM score the student tells you "
    "is a fact about them and may be used anywhere -- it gates the Dövlət Proqramı and the "
    "prep year, both of which are about studying abroad. A predicted DİM cutoff belongs only "
    "to the Azerbaijan section and says nothing about admission in another country; never "
    "carry one into an answer about Germany, the UK or anywhere else.\n"
    "\n"
    "EXPLAIN, DO NOT JUST REPORT. When a route is blocked, say what would open it and what "
    "that costs in months and money -- the tools return both. The single most useful thing "
    "you know is that an attestat holder cannot enter Germany or the UK directly, and that "
    "one year at an Azerbaijani university opens both.\n"
    "\n"
    "You prepare and advise. You MUST NEVER submit an application, and you never promise an "
    "admission outcome."
)


def get_llm():
    """Initialize ChatOpenAI LLM with bound tools if API key is present."""
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        return llm.bind_tools(tools)
    except Exception:
        return None


async def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent decision node processing input messages and determining next action or tool call.
    """
    messages = list(state.get("messages", []))
    
    # Ensure system prompt is present at head of message list
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    last_msg = messages[-1].content if messages else ""

    # Check if document upload keyword / text is present for offline fallback execution
    if "[uploaded document content]" in str(last_msg).lower() or "transcript" in str(last_msg).lower():
        try:
            summary = extract_and_update_profile.invoke({
                "document_text": str(last_msg),
                "student_id": state.get("student_id", "std_demo")
            })
            return {
                "messages": [
                    AIMessage(
                        content=f"I have parsed your uploaded document. {summary} Your application dossier has been updated."
                    )
                ],
                "application_stage": "gathering_info",
                "missing_documents": ["passport_copy", "motivation_letter"]
            }
        except Exception:
            pass

    llm = get_llm()
    if llm is not None:
        try:
            response = await llm.ainvoke(messages)
            return {"messages": [response]}
        except Exception:
            pass

    # Deterministic fallback when offline or with no API key. It describes what the assistant
    # can do and answers nothing -- it must never stand in for a real answer, because a
    # fallback that produces plausible advice is the failure mode this project keeps
    # deleting (ADR-0004).
    return {
        "messages": [
            AIMessage(
                content="I am the AUSA advisor. I can work out which study-abroad routes are "
                        "open, unlockable or blocked for you, what would unlock a blocked one "
                        "and what that costs, which funding you meet the published gates for, "
                        "and what an uploaded transcript says. I cannot answer right now "
                        "because the language model is not reachable — nothing below is a "
                        "result, and I have not assessed anything."
            )
        ]
    }


def create_application_graph():
    """
    Build, connect, and compile the stateful LangGraph application agent workflow.
    """
    workflow = StateGraph(AgentState)

    # 1. Add Agent and Tool Nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # 2. Add Start Edge
    workflow.add_edge(START, "agent")

    # 3. Add Conditional Routing Edges (agent -> tools or agent -> END)
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )

    # 4. Loop tool results back to agent
    workflow.add_edge("tools", "agent")

    # 5. Compile graph
    return workflow.compile()


# Export compiled graph instance
application_agent = create_application_graph()
