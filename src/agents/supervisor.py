import os
from pydantic import BaseModel, Field
import config
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from typing import Literal, List

ROUTES = Literal["hr_policy", "leave_management", "employee_support"]

SUPERVISOR_PROMPT = """You are a routing supervisor for an HR assistant. Classify
the employee's LATEST question into exactly one category, using the
conversation history for context when the latest message alone is
ambiguous (e.g. "tell me again", "confirm", "yes", "what about X").

- hr_policy: questions about what company policy SAYS.
- leave_management: THIS employee's own leave balance, applying for leave,
  leave status, cancelling — INCLUDING short confirmations like "yes",
  "confirm", "go ahead" if the previous assistant turn was asking for
  leave confirmation, and follow-ups like "tell me again" if the previous
  topic was leave-related.
- employee_support: general questions not clearly policy or leave related.

If the latest message is a short confirmation/follow-up, route it to
whichever agent the conversation was already talking to, not employee_support
by default.

Respond with only one word: hr_policy, leave_management, or employee_support.
"""


class RouteDecision(BaseModel):
    agent: ROUTES = Field(..., description="The selected agent.")


def route_question(question: str, history: List[BaseMessage]) -> str:
    llm = ChatGroq(
        model=config.GROQ_MODEL, api_key=os.getenv("GROQ_API_KEY"), temperature=0
    )

    structured_llm = llm.with_structured_output(RouteDecision)

    messages = [SystemMessage(content=SUPERVISOR_PROMPT)]
    messages.extend(history[-6:])
    messages.append(HumanMessage(content=question))

    try:
        decision = structured_llm.invoke(messages)

        return decision.agent
    except Exception:
        return "employee_support"
