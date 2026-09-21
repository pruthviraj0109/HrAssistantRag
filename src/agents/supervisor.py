import os
from pydantic import BaseModel, Field
import config
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from typing import Literal, List

ROUTES = Literal["hr_policy", "leave_management", "employee_support", "onboarding"]

SUPERVISOR_PROMPT = """You are a routing supervisor for an HR assistant. Classify
the employee's LATEST question into exactly one category, using the
conversation history for context when the latest message alone is
ambiguous (e.g. "tell me again", "confirm", "yes", "what about X").

- hr_policy: what company policy SAYS, for anyone. Answered from documents.
  "What is the notice period", "what does the policy say I must submit",
  "how do I submit bank details".

- leave_management: THIS employee's own leave balance, applying for leave,
  leave status, cancelling.

- onboarding: THIS employee's own onboarding checklist and training records.
  What they have done, what is pending or overdue, marking something
  complete, and whether their compliance training has expired.
  "What do I need to do", "what's pending", "my onboarding status",
  "I've submitted my PAN card", "which trainings do I still need",
  "am I up to date on compliance".

- employee_support: general questions not clearly policy, leave or
  onboarding related.

The distinction that matters most:
  what the policy SAYS I must do        -> hr_policy
  what I have not done YET              -> onboarding

If the latest message is a short confirmation or follow-up ("yes",
"confirm", "go ahead", "tell me again"), route it to whichever agent the
conversation was already talking to — never employee_support by default.

Respond with only one word: hr_policy, leave_management, onboarding,
or employee_support.
"""


class RouteDecision(BaseModel):
    agent: ROUTES = Field(..., description="The selected agent.")


_llm = ChatGroq(
    model=config.GROQ_MODEL, api_key=os.getenv("GROQ_API_KEY"), temperature=0
)

_router = _llm.with_structured_output(RouteDecision)


def route_question(question: str, history: List[BaseMessage]) -> str:
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)]

    if history:
        messages.extend(history[-6:])
    else:
        messages.append(HumanMessage(content=question))

    try:
        decision = _router.invoke(messages)

        return decision.agent
    except Exception:
        return "employee_support"
