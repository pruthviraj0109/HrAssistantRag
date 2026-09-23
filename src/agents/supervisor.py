import os
from pydantic import BaseModel, Field
import config
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from typing import Literal, List

ROUTES = Literal[
    "hr_policy",
    "leave_management",
    "onboarding",
    "employee_support",
]

SUPERVISOR_PROMPT = """You are a routing supervisor for an HR assistant. Classify
the employee's LATEST question into exactly one category, using the
conversation history for context when the latest message alone is
ambiguous (e.g. "tell me again", "confirm", "yes", "what about X").
 
- hr_policy: ANYTHING that could be answered from an uploaded document.
  This is the DEFAULT for factual questions. It covers:
    * what a policy says — notice period, working hours, leave rules,
      dress code, grievance process
    * the COMPANY ITSELF — its name, address, offices, branches,
      registered details, contact details
    * recruitment, hiring, the selection or interview process
    * procedures — how to submit something, who to approach, what a
      document requires
  "What is the notice period." "What is the company name."
  "Tell me the company address." "What is the selection process."
  "How do I submit my bank details." "Who do I contact about a grievance."
 
- leave_management: THIS employee's own leave — balance, applying for
  leave, leave status, cancelling.
  "How many leaves do I have." "I want to apply for sick leave."
 
- onboarding: THIS employee's own onboarding checklist and training
  records. What they have done, what is pending or overdue, marking
  something complete, and whether their compliance training has expired.
  "What do I need to do." "What's pending." "My onboarding status."
  "I've submitted my PAN card." "Which trainings do I still need."
  "Am I up to date on compliance."
 
- employee_support: greetings, small talk, thanks, and messages that ask
  no factual question at all. This is a NARROW category, not a fallback.
  "Hi." "Hello." "Thanks." "What can you help me with."
 
Three distinctions that matter:
 
  a factual question about the company or its rules  -> hr_policy
  what I have or have not done YET                   -> leave or onboarding
  a greeting or small talk                           -> employee_support
 
Only employee_support has NO document search and NO database access, so a
factual question sent there cannot be answered at all. When a question is
factual and you are unsure which agent owns it, choose hr_policy.
 
If the latest message is a short confirmation or follow-up ("yes",
"confirm", "go ahead", "done", "tell me again", "in short"), route it to
whichever agent the conversation was already talking to. Never default to
employee_support for these.
 
Respond with exactly one of: hr_policy, leave_management, onboarding,
employee_support.
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
