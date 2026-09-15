"""
LLM-as-a-judge: uses an LLM to automatically score RAG answers instead of
a human reading each one manually. Scores Faithfulness (is the answer
grounded in the retrieved context?) and Relevance (does it actually answer
the question?) on a 1-5 scale, with a short justification.
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

import config

JUDGE_SYSTEM_PROMPT = """You are an impartial evaluator of AI-generated answers.

You will be given:
- A QUESTION asked by a user
- The CONTEXT that was retrieved from documents to answer it
- The ANSWER that was generated

Score the answer on two dimensions, each from 1 (very poor) to 5 (excellent):

1. FAITHFULNESS: Is every claim in the answer actually supported by the
   CONTEXT? A score of 1 means the answer contains information not found
   in the context (hallucination). A score of 5 means every claim is
   directly backed by the context. If the context says the information
   was not found and the answer correctly says so too, that is faithful
   and should score 5.

2. RELEVANCE: Does the answer actually address what the QUESTION asked?
   A score of 1 means it's off-topic or unhelpful. A score of 5 means it
   directly and completely answers the question.

Respond with ONLY valid JSON in this exact format, nothing else, no markdown:
{
  "faithfulness_score": <integer 1-5>,
  "faithfulness_reason": "<one sentence explaining the score>",
  "relevance_score": <integer 1-5>,
  "relevance_reason": "<one sentence explaining the score>"
}
"""


def get_judge_llm():
    return ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0, 
    )


def judge_answer(question: str, context: str, answer: str) -> dict:
    """Sends one Q/context/answer triple to the judge LLM and returns parsed scores."""
    judge_llm = get_judge_llm()

    user_prompt = f"""QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
{answer}
"""

    response = judge_llm.invoke(
        [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    raw_text = response.content.strip()

    # Strip markdown code fences if the model wraps its JSON in ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "faithfulness_score": None,
            "faithfulness_reason": f"Could not parse judge output: {raw_text[:200]}",
            "relevance_score": None,
            "relevance_reason": "Parse error",
        }
