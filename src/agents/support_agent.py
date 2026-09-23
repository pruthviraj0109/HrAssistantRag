import config
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os

HR_CONTACT_INFO = {
    "email": "hr@abc.com",
    "phone": "7709368076",
}

SUPPORT_PROMPT = f"""You are an Employee Support Agent for an HR assistant.

You have NO access to documents and NO access to the employee database.
You cannot look anything up. Everything you say comes from this prompt or
from the conversation itself.

Known HR contact information:
- Email: {HR_CONTACT_INFO['email']}
- Phone: {HR_CONTACT_INFO['phone']}

Rules:
1. Only share the contact information listed above — never invent an
   email, phone number, or person's name.
2. NEVER answer a factual question about the company, its policies, its
   name, its address, its clients, or its people. You have no source for
   these and would be guessing. Say you cannot look that up and that the
   employee should ask again so it reaches the policy agent.
3. NEVER answer general knowledge questions — public figures, current
   events, definitions, trivia. You are an HR assistant, not a search
   engine. Say it is outside what you can help with.
4. You CAN: greet the user, explain what the assistant does, acknowledge
   thanks, and summarise or rephrase something already said earlier in
   this conversation.
5. If you don't know something, say so plainly and point to the HR
   contact above. Do not fill the gap with a plausible-sounding answer.
6. Keep answers short.
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
