import config

from sqlalchemy.orm import Session
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
)

from src.tools.leave_tools import build_leave_tools

LEAVE_AGENT_PROMPT = """
You are a Leave Management Agent for an HR system.

Use the conversation history carefully.

Rules:

1. Only act on the authenticated employee's own leave data.

2. For leave balance questions, call the appropriate balance tool.

3. For a new leave request:
   - Extract the leave type.
   - Extract start date.
   - Extract end date.
   - Validate the request.
   - Show the summary.
   - Wait for confirmation.

4. If the user says:
   - yes
   - confirm
   - confirmed
   - go ahead
   - submit
   - proceed

   then treat it as confirmation only when the previous conversation
   contains a pending leave request summary.

5. If the user asks "what", "what?", "what do you mean?",
   or gives an unclear message, ask for clarification.

6. Do not ask for leave details again if the previous conversation
   already contains the complete leave request.

7. Never invent leave balances or leave request details.

8. Do not submit a leave request unless the user explicitly confirms.
"""


def run_leave_agent(
    db: Session,
    user_id: int,
    question: str,
    messages: list[BaseMessage] | None = None,
) -> dict:

    tools = build_leave_tools(
        db,
        user_id,
    )

    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,
    )

    agent = create_agent(
        model=llm,
        tools=tools,
    )

    agent_messages = [
        SystemMessage(content=LEAVE_AGENT_PROMPT),
    ]

    if messages:
        agent_messages.extend(messages[-12:])

    agent_messages.append(HumanMessage(content=question))

    result = agent.invoke(
        {
            "messages": agent_messages,
        }
    )

    answer = result["messages"][-1].content

    return {
        "agent_response": answer,
    }
