import re
from typing import List, Dict


def clean_text(text: str) -> str:
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_documents(pages: List[Dict]) -> List[Dict]:
    cleaned = []
    for page in pages:
        cleaned.append(
            {
                **page,
                "text": (page["text"]),
            }
        )
    return [p for p in cleaned if p["text"]]
