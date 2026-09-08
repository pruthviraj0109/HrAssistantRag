from typing import List, Dict

from langchain_text_splitters import CharacterTextSplitter


def chunk_fixed_size(
    pages: List[Dict],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict]:

    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    chunk_id = 0

    for page in pages:

        for piece in splitter.split_text(page["text"]):

            chunks.append(
                {
                    "chunk_id": f"fixed_{chunk_id}",
                    "text": piece,
                    "source": page["source"],
                    "page_number": page.get("page_number"),
                    "strategy": "fixed_size",
                }
            )

            chunk_id += 1

    return chunks