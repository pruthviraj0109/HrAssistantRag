from typing import List, Dict


def compare_strategies(fixed_chunks: List[Dict], recursive_chunks: List[Dict]) -> str:
    def stats(chunks: List[Dict]):
        lengths = [len(c["text"]) for c in chunks]
        return {
            "count": len(chunks),
            "avg_len": sum(lengths) / len(lengths) if lengths else 0,
            "min_len": min(lengths) if lengths else 0,
            "max_len": max(lengths) if lengths else 0,
        }

    fixed_stats = stats(fixed_chunks)
    recursive_stats = stats(recursive_chunks)

    report = f"""
Chunking Strategy Comparison
-----------------------------
Fixed-size chunking:
  Total chunks : {fixed_stats['count']}
  Avg length   : {fixed_stats['avg_len']:.1f} chars
  Min / Max    : {fixed_stats['min_len']} / {fixed_stats['max_len']}

Recursive chunking:
  Total chunks : {recursive_stats['count']}
  Avg length   : {recursive_stats['avg_len']:.1f} chars
  Min / Max    : {recursive_stats['min_len']} / {recursive_stats['max_len']}

Observation:
Fixed-size chunking produces more uniform chunk lengths but can cut sentences
or policy clauses mid-way. Recursive chunking respects paragraph/section
boundaries, producing more semantically coherent chunks at the cost of
uneven sizes.
"""
    return report.strip()
