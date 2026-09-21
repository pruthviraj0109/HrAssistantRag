import re
from datetime import date

import config

from sqlalchemy.orm import Session
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
)

from src.tools.onboarding_tools import build_onboarding_tools

ONBOARDING_AGENT_PROMPT = """
You are an Onboarding and Training Agent for an HR system.

Today's date is {today}.

Use the conversation history carefully.

Rules:

1. Only act on the authenticated employee's own records. The employee is already
   identified by their login.

2. NEVER ask the user for an employee ID, user ID, or to confirm their login.
   If a tool reports that no record exists, tell the user their onboarding record
   has not been set up and to contact HR. Do not ask them for identifying details.

3. For "what do I need to do", "what is pending", "onboarding status" questions,
   call check_onboarding_status.

4. For "what training do I need", "am I up to date on compliance" questions,
   call check_training_status.

5. Marking something complete changes the record. Before calling
   mark_task_complete or mark_training_complete:
   - Say which item you are about to mark.
   - Wait for the user to confirm.
   - Only then call the tool with confirmed=True.

6. Treat these as confirmation, but only when the previous turn asked for it:
   yes, confirm, confirmed, go ahead, done, that's done, proceed.

7. If the user says they have done something but does not name which item
   clearly, ask which task they mean. Do not guess.

8. Never invent tasks, training courses, due dates or completion dates. If a tool
   does not return it, you do not know it.

9. If the user asks HOW to complete a task — where to submit a document, how to
   access a course — say that the detail is in the onboarding policy documents.
   You hold status, not instructions.

10. Lead with what is overdue. If nothing is overdue, say so.

11. NEVER state that something has been marked complete unless the tool returned
    a success message naming that exact item. Not "probably", not "should now be".
    If you did not call the tool, nothing was marked. If the tool returned an
    error, nothing was marked — say what the error was.

12. If the user names SEVERAL items in one message, pass them all to the tool in
    a single call. Do not mark one and describe the rest as done. Report exactly
    what the tool returned, item by item.

13. After any write, call check_onboarding_status or check_training_status again
    and report the fresh list. Do not describe the remaining items from memory.
"""


_llm = ChatGroq(
    model=config.GROQ_MODEL,
    api_key=config.GROQ_API_KEY,
    temperature=0,
)

WRITE_TOOLS = {"mark_task_complete", "mark_training_complete"}

_CLAIM = re.compile(
    r"(marked?\s+(as\s+)?(complete|completed|done|submitted)"
    r"|has\s+been\s+marked"
    r"|now\s+(marked\s+)?complete"
    r"|all\s+(pending\s+)?tasks\s+are\s+now\s+(finished|complete))",
    re.IGNORECASE,
)


def run_onboarding_agent(
    db: Session,
    user_id: int,
    question: str,
    messages: list[BaseMessage] | None = None,
) -> dict:

    tools = build_onboarding_tools(db, user_id)

    agent = create_agent(model=_llm, tools=tools)

    agent_messages = [
        SystemMessage(
            content=ONBOARDING_AGENT_PROMPT.format(today=date.today().isoformat())
        )
    ]

    if messages:

        agent_messages.extend(messages[-12:])
    else:
        agent_messages.append(HumanMessage(content=question))

    result = agent.invoke({"messages": agent_messages})
    answer = result["messages"][-1].content

    write_results = [
        str(m.content)
        for m in result["messages"]
        if getattr(m, "name", "") in WRITE_TOOLS
    ]
    succeeded = [r for r in write_results if "marked complete" in r]
    asked_to_confirm = any("Not marked" in r for r in write_results)

    if _CLAIM.search(answer) and not succeeded:
        print(
            "ONBOARDING GUARD: model claimed a completion with no successful "
            f"write. user_id={user_id} tool_results={write_results}"
        )
        if write_results:
            answer = "I could not update your record:\n\n" + "\n".join(
                f"- {r}" for r in write_results
            )
        else:
            answer = (
                "Nothing has been marked complete yet — I did not update your "
                "record. Please tell me exactly which item you want marked, "
                "and confirm, and I will update it."
            )

    awaiting = asked_to_confirm and not succeeded

    return {
        "agent_response": answer,
        "awaiting_confirmation": awaiting,
        "pending_agent": "onboarding" if awaiting else None,
    }


run_onboard_agent = run_onboarding_agent
