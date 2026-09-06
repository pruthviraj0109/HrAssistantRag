from langchain.tools import tool
from src.retrieval.vector_store import load_vector_store

POLICY_METADATA = {
    "Leave & Attendance Policy": {"version": "v2.1", "effective_date": "2025-01-01"},
    "Work From Home Policy": {"version": "v1.3", "effective_date": "2024-06-15"},
    "Travel & Expense Policy": {"version": "v3.0", "effective_date": "2025-04-01"},
}


_vector_store = None


def _get_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = load_vector_store()
        return _vector_store


@tool
def document_metadata(chunk_id: str) -> str:
    store = _get_store()
    collection = store.get(where={"chunk_id": chunk_id})

    if not collection or not collection.get("metadatas"):
        return f"No metadata found for chunk_id '{chunk_id}'."

    meta = collection["metadatas"][0]
    source = meta.get("source", "unknown")
    extra = POLICY_METADATA.get(source, {})

    return (
        f"Source: {source}\n"
        f"Page: {meta.get('page_number')}\n"
        f"Chunking strategy: {meta.get('strategy')}\n"
        f"Version: {extra.get('version', 'not tracked')}\n"
        f"Effective date: {extra.get('effective_date', 'not tracked')}"
    )
