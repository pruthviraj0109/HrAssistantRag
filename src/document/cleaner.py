import re

from typing import List, Dict


def clean_text(text: str) -> str:

   
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_documents(pages: List[Dict]) -> List[Dict]:

    cleaned = []

    for page in pages:

        text = clean_text(page["text"])

        if text:

            cleaned.append(
                {
                    **page,
                    "text": text,
                }
            )

    return cleaned