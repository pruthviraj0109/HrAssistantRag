from langchain_core.tools import tool

from src.retrieval.vector_store import load_vector_store



POLICY_METADATA = {
    "HR Policy _ KESPL.pdf": {
        "version": "v2.1",
        "effective_date": "2025-01-01",
    },
    "Work From Home Policy": {
        "version": "v1.3",
        "effective_date": "2024-06-15",
    },
    "Travel & Expense Policy": {
        "version": "v3.0",
        "effective_date": "2025-04-01",
    },
}



_vector_store = None


def _get_store():
    global _vector_store

    if _vector_store is None:
        _vector_store = load_vector_store()

    return _vector_store


@tool
def document_metadata(chunk_id: str) -> str:
    """
    Retrieve metadata for an HR policy document chunk.

    Use this tool when the user asks about:
    - document details
    - document version
    - effective date
    - document origin/source
    - page information
    - details about a previously retrieved chunk
    """

    store = _get_store()

    collection = store.get(
        where={"chunk_id": chunk_id},
        include=["metadatas"],
    )

    metadatas = collection.get("metadatas", [])

    if not metadatas:
        return f"No metadata found for chunk_id '{chunk_id}'."

    meta = metadatas[0]

    source = meta.get("source", "unknown")
    page_number = meta.get("page_number", "unknown")
    strategy = meta.get("strategy", "unknown")
    stored_chunk_id = meta.get("chunk_id", chunk_id)

  
    extra = POLICY_METADATA.get(source, {})

    version = extra.get("version", "not tracked")
    effective_date = extra.get("effective_date", "not tracked")

    return (
        f"Source: {source}\n"
        f"Page: {page_number}\n"
        f"Chunk ID: {stored_chunk_id}\n"
        f"Chunking strategy: {strategy}\n"
        f"Version: {version}\n"
        f"Effective date: {effective_date}"
    )