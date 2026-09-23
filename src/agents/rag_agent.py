from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

import config

from src.agents.memory import ConversationMemory
from src.tools.factory import build_tools

MAX_HISTORY_MESSAGES = 6
MAX_TOOLS_CALLS = 2


SYSTEM_PROMPT_TEMPLATE = """You are a {domain} assistant.
 
You have these tools available:
 
- document_search: use this for any question about policy content
  (what the rules/benefits/procedures actually say). Pass the user's
  question as the 'query' argument.
 
- document_metadata: use this only when the user asks about a document's
  version, effective date, or origin/source — not for content questions.
  This tool requires a chunk_id, which you get from a prior
  document_search result. Never call this without a real chunk_id.
 
- add_numbers: use this ONLY for simple arithmetic addition questions
  (e.g. "what is 5 plus 3"). Never use this for anything else.
 
- get_current_weather: use this ONLY when the user explicitly asks about
  current weather in a specific city.
 
- web_search: use this ONLY for general knowledge questions that are
  clearly unrelated to the uploaded documents (e.g. current events,
  general trivia) — and only after document_search has been tried and
  found nothing relevant, if the question could plausibly relate to the
  documents.
 
- get_current_datetime: use this ONLY when the user explicitly asks what
  today's date or the current time is.
 
Rules you must always follow:
1. Only answer using information retrieved via your tools — never guess
   or make up an answer.
2. Pick the SINGLE most appropriate tool for the question. Do not call
   multiple unrelated tools for one simple question.
3. Call document_search AT MOST TWICE per question. If the second search
   does not return the answer, stop and say: "I could not find this
   information in the available documents." Searching a third time with a
   shorter query has never helped and makes the request too large.
4. If document_search does not contain the answer to a policy question,
   say clearly: "I could not find this information in the available
   documents." Do not fall back to web_search for policy questions.
5. Always cite the source document (and page number, if available) when
   answering from document_search.
6. Use conversation history to resolve follow-up questions.
7. Keep answers concise. Do not repeat the retrieved text back in full —
   answer the question and cite the source.
"""

FALLBACK_ANSWER = (
    "I'm hitting a rate limit at the moment. " "Please try that again in a few seconds."
)


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
        messages = [SystemMessage(content=self.system_prompt)]
        history = self.memory.get_messages()

        if history:
            messages.extend(history[-MAX_HISTORY_MESSAGES:])

        messages.append(HumanMessage(content=question))

        try:
            result = self.executor.invoke(
                {"messages": messages},
                {"recursion_limit": (MAX_TOOLS_CALLS * 2) + 2},
            )
            answer = result["messages"][-1].content

        except Exception as e:
            msg = str(e)

            # anything that is NOT a rate limit is a real error — let it
            # propagate so the traceback is not swallowed
            if not any(
                k in msg for k in ("rate_limit", "413", "429", "Request too large")
            ):
                raise

            self.memory.clear()
            try:
                result = self.executor.invoke(
                    {
                        "messages": [
                            SystemMessage(content=self.system_prompt),
                            HumanMessage(content=question),
                        ]
                    },
                    {"recursion_limit": 4},
                )
                answer = result["messages"][-1].content
            except Exception:
                return FALLBACK_ANSWER

        if not answer:
            answer = (
                "I could not produce an answer for that. "
                "Please try rephrasing the question."
            )

        self.memory.add_user_message(question)
        self.memory.add_ai_message(answer)

        return answer
