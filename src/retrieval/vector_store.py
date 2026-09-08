from typing import List, Dict

from langchain_chroma import Chroma
from langchain_core.documents import Document

import config
from src.embeddings.embedder import get_embedding_function


def build_vector_store(chunks: List[Dict]) -> Chroma:

    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "source": chunk["source"],
                "page_number": chunk.get("page_number") or 0,
                "chunk_id": chunk["chunk_id"],
                "strategy": chunk.get("strategy", "unknown"),
            },
        )
        for chunk in chunks
    ]

    if not documents:
        raise ValueError("No documents/chunks were created for the vector store.")

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=get_embedding_function(),
        collection_name=config.CHROMA_COLLECTION_NAME,
        persist_directory=str(config.CHROMA_DIR),
    )

    return vector_store


def load_vector_store() -> Chroma:

    return Chroma(
        collection_name=config.CHROMA_COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=str(config.CHROMA_DIR),
    )


def top_k_search(
    vector_store: Chroma,
    query: str,
    k: int = config.TOP_K,
) -> List[Document]:

    return vector_store.similarity_search(query, k=k)
