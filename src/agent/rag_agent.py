from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

import config

from src.tools.document_search_tool import document_search
from src.tools.metadata_tool import document_metadata
from src.agent.memory import ConversationMemory

SYSTEM_PROMPT = """
You are an HR Policy Assistant.

Rules:

1. For HR policy content questions, ALWAYS use the document_search tool first.

2. Only answer HR policy questions using information found in the retrieved
   HR policy documents.

3. If the retrieved documents do not contain the answer, respond exactly:

"I could not find this information in the available HR policy documents."

4. Never guess or invent HR policy information.

5. Always cite the source document and page number when available.

6. Use document_metadata when the user asks about:
   - document version
   - effective date
   - document origin
   - source information
   - page information
   - document details
   - chunk details
   - metadata of a previously retrieved document/chunk

7. If the user says:
   - "this document"
   - "this chunk"
   - "that document"
   - "that chunk"
   - "the document"
   - "the chunk"
   - "tell me more about it"
   - or similar follow-up wording,

   use the conversation history to identify the most recently referenced
   chunk_id from a previous document_search result.

   Then call document_metadata using that chunk_id.

8. Do NOT call document_metadata unless you have a valid chunk_id from the
   conversation or from a document_search result.

9. Use conversation history to understand follow-up questions.

10. For follow-up questions about the content of the same policy, use the
    previous conversation context to understand what the user is referring to.

11. If the user asks for personal information such as their name, answer only
    if that information exists in the available HR policy documents.
    Otherwise use the standard not-found response.

12. Do not invent a chunk_id.

13. When answering using document_search results, preserve source and page
    information whenever available.
"""


def build_agent():

    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,
    )

    tools = [
        document_search,
        document_metadata,
    ]

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


class RagAgent:

    def __init__(self):

        self.executor = build_agent()

        self.memory = ConversationMemory()

    def ask(self, question: str) -> str:

        messages = self.memory.get_messages()[-10:]

        messages = messages + [HumanMessage(content=question)]

        result = self.executor.invoke({"messages": messages})

        answer = result["messages"][-1].content

        self.memory.add_user_message(question)
        self.memory.add_ai_message(answer)

        return answer
