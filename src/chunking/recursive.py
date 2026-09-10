from typing import List, Dict
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_recursive(
    pages: List[Dict],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []

    for page in pages:

        for piece in splitter.split_text(page["text"]):

            chunks.append(
                {
                    "chunk_id": f"recursive_{uuid.uuid4().hex[:12]}",
                    "text": piece,
                    "source": page["source"],
                    "page_number": page.get("page_number"),
                    "strategy": "recursive",
                }
            )

    return chunks
