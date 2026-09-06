import sys
from pathlib import Path

from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from src.agent.rag_agent import RagAgent
from evaluation.test_questions import TEST_QUESTIONS


def run_eval():
    config.EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    agent = RagAgent()

    lines = [f"# Evaluation Results — {datetime.now().isoformat(timespec='seconds')}\n"]

    for item in TEST_QUESTIONS:
        answer = agent.ask(item["question"])
        lines.append(f"## Q{item['id']} [{item['category']}]")
        lines.append(f"**Question:** {item['question']}")
        lines.append(f"**Answer:** {answer}")
        lines.append("")

        output_path = config.EVAL_RESULTS_DIR / "eval_results.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evaluation complete. Results saved to {output_path}")


if __name__ == "__main__":
    run_eval()
