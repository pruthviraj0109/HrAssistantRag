from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_recursive(
    pages: List[Dict], chunk_size: int, chunk_overlap: int
) -> List[Dict]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []

    chunk_id = 0
    for page in pages:
        for piece in splitter.split_text(page["text"]):
            chunks.append(
                {
                    "chunk_id": f"recursive_{chunk_id}",
                    "text": piece,
                    "source": page["source"],
                    "page_number": page.get("page_number"),
                    "stratergy": "recursive",
                }
            )
            chunk_id += 1
    return chunks
