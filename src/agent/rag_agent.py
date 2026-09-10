from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage,SystemMessage

import config

from src.agent.memory import ConversationMemory
from src.tools.factory import build_tools
#

SYSTEM_PROMPT_TEMPLATE = """You are a {domain} assistant.

You have two tools available:
- document_search: use this for any question about policy content
  (what the rules/benefits/procedures actually say).
- document_metadata: use this only when the user asks about a document's
  version, effective date, or origin/source — not for content questions.
  This tool requires a chunk_id, which you can get from a prior
  document_search result.

Rules you must always follow:
1. Only answer using information retrieved via your tools — never guess
   or make up an answer.
2. If the retrieved context does not contain the answer, say clearly:
   "I could not find this information in the available documents."
3. Always cite the source document (and page number, if available).
4. Use conversation history to resolve follow-up questions.
"""


class RagAgent:

    def __init__(self, vector_store, domain: str):
        tools = build_tools(vector_store)
        llm = ChatGroq(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            temperature=0,
        )

        self.executor = create_agent(llm, tools)
        self.memory = ConversationMemory()
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(domain=domain)

    def ask(self, question: str) -> str:
        messages=[SystemMessage(content=self.system_prompt)]
        messages.extend(self.memory.get_messages())


        messages.append(HumanMessage(content=question)) 

        result = self.executor.invoke({"messages": messages})

        answer = result["messages"][-1].content

        self.memory.add_user_message(question)
        self.memory.add_ai_message(answer)

        return answer
