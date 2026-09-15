from typing import List, Dict
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document

import config
from src.embeddings.embedder import get_embedding_function


def add_chunks_to_vector_store(
    chunks: List[Dict],
    persist_dir: Path,
    collection_name: str,
    username: str,
    domain: str,
) -> Chroma:

    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "source": chunk["source"],
                "page_number": chunk.get("page_number") or 0,
                "chunk_id": chunk["chunk_id"],
                "strategy": chunk.get("strategy", "unknown"),
                "user_id": username,
                "domain": domain,
            },
        )
        for chunk in chunks
    ]

    if not documents:
        raise ValueError("No documents/chunks were created for the vector store.")

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=get_embedding_function(),
        persist_directory=str(persist_dir),
    )

    vector_store.add_documents(documents)

    return vector_store


def load_vector_store(persist_dir: Path, collection_name: str) -> Chroma:

    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embedding_function(),
        persist_directory=str(persist_dir),
    )


def top_k_search(
    vector_store: Chroma,
    query: str,
    k: int = config.TOP_K,
) -> List[Document]:

    return vector_store.similarity_search(query, k=k)
