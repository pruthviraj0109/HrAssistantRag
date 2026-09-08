from langchain_core.tools import tool
from src.retrieval.vector_store import load_vector_store, top_k_search

_vector_store = None


def _get_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = load_vector_store()
    return _vector_store


@tool
def document_search(query: str) -> str:
    """Search the HR policy documents and return relevant policy information with source and page citations."""

    store = _get_store()
    results = top_k_search(store, query)

    if not results:
        return "NO_RELEVANT_CHUNKS_FOUND"

    formatted = []

    for doc in results:
        meta = doc.metadata

        formatted.append(
            f"[Source: {meta.get('source')} | "
            f"Page: {meta.get('page_number')} | "
            f"Chunk ID: {meta.get('chunk_id')}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(formatted)
