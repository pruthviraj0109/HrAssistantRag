from pathlib import Path
from typing import List, Dict
import pdfplumber
import docx


def load_pdf(path: Path) -> List[Dict]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(
                    {
                        "text": text,
                        "page_number": 1,
                        "source": path.name,
                    }
                )
    return pages


def load_docx(path: Path) -> List[Dict]:
    document = docx.Document(path)

    text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
    if not text.strip():
        return []
    return [{"text": text, "page_number": None, "source": path.name}]


def load_txt(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return []
    return [{"text": text, "page_number": None, "source": path.name}]


def load_documents(data_dir: Path) -> List[Dict]:
    all_pages = []
    for path in sorted(data_dir.glob("*")):
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            all_pages.extend(load_pdf(path))
        elif suffix == ".docx":
            all_pages.extend(load_documents(path))
        elif suffix == ".txt":
            all_pages.extend(load_txt(path))
    return all_pages
