from typing import Annotated, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State definition for the University Application Agent stateful workflow.
    
    Attributes:
        messages: List of LangChain message objects with add_messages reducer for chat history.
        student_id: Primary identifier for the student.
        target_program_id: Primary identifier for the target university program.
        missing_documents: List of document names currently missing from student's dossier.
        application_stage: Current stateful stage ("gathering_info", "drafting_documents", "ready_to_submit").
    """
    messages: Annotated[List[BaseMessage], add_messages]
    student_id: Optional[str]
    target_program_id: Optional[str]
    missing_documents: List[str]
    application_stage: str
