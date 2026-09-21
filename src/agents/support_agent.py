import config
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os

HR_CONTACT_INFO = {
    "email": "hr@abc.com",
    "phone": "7709368076",
}

SUPPORT_PROMPT = f"""You are an Employee Support Agent for an HR assistant.

Known HR contact information:
- Email: {HR_CONTACT_INFO['email']}
- Phone: {HR_CONTACT_INFO['phone']}

Rules:
1. Only share the contact information listed above — never invent an email,
   phone number, or person's name that isn't given to you here.
2. If you don't know the answer to something, say so plainly and suggest
   the employee contact HR directly using the information above.
3. Keep answers short and helpful.
"""


def run_support_agent(
    question: str,
    messages=None,
) -> dict:

    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    conversation = [
        SystemMessage(content=SUPPORT_PROMPT),
    ]

    if messages:
        conversation.extend(messages[-6:])

    conversation.append(HumanMessage(content=question))

    response = llm.invoke(conversation)

    return {"agent_response": response.content}
