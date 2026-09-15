"""
Runs the test question suite through the agent, then scores each answer
using an LLM judge instead of manual review. Saves results to a Markdown
report with per-question scores and an overall average.

Run with:
    python evaluation/run_llm_judge_eval.py
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from src.retrieval.vector_store import load_vector_store
from src.tools.factory import build_tools
from src.agent.rag_agent import RagAgent
from evaluation.test_questions import TEST_QUESTIONS
from evaluation.llm_judge import judge_answer


def run_llm_judge_evaluation(username: str, domain: str):
    vectorstore_dir = config.get_vectorstore_dir(username, domain)
    collection_name = config.get_collection_name(username, domain)
    vector_store = load_vector_store(vectorstore_dir, collection_name)

    tools = build_tools(vector_store)
    document_search = tools[0]  # used to capture context separately, for scoring

    agent = RagAgent(vector_store, domain)

    results = []

    for item in TEST_QUESTIONS:
        question = item["question"]
        print(f"Evaluating: {question}")

        answer = agent.ask(question)
        context = document_search.func(question)

        scores = judge_answer(question, context, answer)

        results.append(
            {
                "id": item["id"],
                "category": item["category"],
                "question": question,
                "answer": answer,
                **scores,
            }
        )

    # --- Build a readable Markdown report ---
    lines = [
        f"# LLM-as-Judge Evaluation Results — {datetime.now().isoformat(timespec='seconds')}\n"
    ]

    valid_faithfulness = [
        r["faithfulness_score"] for r in results if r["faithfulness_score"] is not None
    ]
    valid_relevance = [
        r["relevance_score"] for r in results if r["relevance_score"] is not None
    ]

    avg_faithfulness = (
        sum(valid_faithfulness) / len(valid_faithfulness) if valid_faithfulness else 0
    )
    avg_relevance = (
        sum(valid_relevance) / len(valid_relevance) if valid_relevance else 0
    )

    lines.append(f"**Average Faithfulness:** {avg_faithfulness:.2f} / 5")
    lines.append(f"**Average Relevance:** {avg_relevance:.2f} / 5\n")

    for r in results:
        lines.append(f"## Q{r['id']} [{r['category']}]")
        lines.append(f"**Question:** {r['question']}")
        lines.append(f"**Answer:** {r['answer']}")
        lines.append(
            f"**Faithfulness:** {r['faithfulness_score']}/5 — {r['faithfulness_reason']}"
        )
        lines.append(
            f"**Relevance:** {r['relevance_score']}/5 — {r['relevance_reason']}"
        )
        lines.append("")

    config.EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = config.EVAL_RESULTS_DIR / "llm_judge_results.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nAverage Faithfulness: {avg_faithfulness:.2f}/5")
    print(f"Average Relevance: {avg_relevance:.2f}/5")
    print(f"Full report saved to {output_path}")


if __name__ == "__main__":
    run_llm_judge_evaluation(username="aditya@gmail.com", domain="hr")
