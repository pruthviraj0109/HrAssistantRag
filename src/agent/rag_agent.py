from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

import config
from src.tools.document_search_tool import document_search
from src.tools.metadata_tool import document_metadata
from src.agent.memory import ConversationMemory

SYSTEM_PROMPT = """You are an HR Policy Assistant.

Rules you must always follow:
1. Only answer using information retrieved via the document_search tool.
2. If the retrieved context does not contain the answer, say clearly:
   "I could not find this information in the available HR policy documents."
   Do NOT guess or make up an answer.
3. Always cite the source document (and page number, if available) for any
   fact you state.
4. Use document_metadata only when the user asks about a document's version,
   effective date, or origin — not for answering policy content questions.
5. Use conversation history to resolve follow-up questions (e.g. pronouns
   like "it" or implicit references to the previous topic).
"""


def build_agent():
    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,
    )

    tools = [document_search, document_metadata]
    return create_agent(llm, tools)


class RagAgent:

    def __init__(self):
        self.executor = build_agent()
        self.memory = ConversationMemory()

    def ask(self, question: str) -> str:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(self.memory.get_messages())
        messages.append(HumanMessage(content=question))

        result = self.executor.invoke({"messages": messages})
        answer = result["messages"][-1].content

        self.memory.add_user_message(question)
        self.memory.add_ai_message(answer)
        return answer
