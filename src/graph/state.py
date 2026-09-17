from typing import TypedDict, Optional, List, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class HRState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]

    question: str
    user_id: int
    username: str

    selected_agent: Optional[str]
    agent_response: Optional[str]
    sources: Optional[List[dict]]
    final_answer: Optional[str]
    error: Optional[str]

    pending_leave: Optional[Dict[str, Any]]
    awaiting_confirmation: bool
