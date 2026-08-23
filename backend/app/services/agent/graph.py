from typing import Any, Dict
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.services.agent.state import AgentState
from app.services.agent.tools import tools

SYSTEM_PROMPT = (
    "You are an expert AI University Application Advisor for Azerbaijani students studying abroad. "
    "Your goal is to guide students step-by-step through preparing their university application dossier. "
    "You have tools to check missing documents, look up program deadlines, and draft motivation letters. "
    "Assisting and preparing documents is your role — you MUST NEVER attempt to automatically submit applications."
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

    llm = get_llm()
    if llm is not None:
        try:
            response = await llm.ainvoke(messages)
            return {"messages": [response]}
        except Exception:
            pass

    # Deterministic fallback response when offline / API key unconfigured
    last_msg = messages[-1].content if messages else ""
    return {
        "messages": [
            AIMessage(
                content=f"I am your AI Application Advisor. I can help check missing documents, "
                        f"find deadlines, and draft your motivation letter."
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
