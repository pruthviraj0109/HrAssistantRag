
from langchain_core.tools import tool
from langchain_core.tools import tool, StructuredTool
from src.retrieval.vector_store import top_k_search

# Extend this as real policy documents gain version numbers / effective dates.
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


def build_tools(vector_store):
    def document_search(query: str) -> str:
        """Search the uploaded documents for this user and domain, and
        return relevant information with source and page citations."""
        results = top_k_search(vector_store, query)
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

    def document_metadata(chunk_id: str) -> str:
        """
        Retrieve metadata for a document chunk: source, page, chunking
        strategy, and (if tracked) policy version and effective date.
        Use this only when the user asks about document version, effective
        date, origin, or details about a previously retrieved chunk.
        """
        collection = vector_store.get(where={"chunk_id": chunk_id}, include=["metadatas"])
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

    search_tool = StructuredTool.from_function(
        func=document_search,
        name="document_search",
        description="Searches the user's uploaded documents for this domain. Use for any content question.",
    )
    metadata_tool = StructuredTool.from_function(
        func=document_metadata,
        name="document_metadata",
        description="Retrieves metadata about a specific chunk (source, page, version, effective date). Use only for version/origin questions.",
    )
    return [search_tool, metadata_tool]