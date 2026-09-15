from pathlib import Path
from typing import List, Dict
import pdfplumber
import docx

from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem


def load_pdf_pdfplumber(path: Path) -> List[Dict]:
    pages = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                pages.append(
                    {
                        "text": text,
                        "page_number": i,
                        "source": path.name,
                    }
                )

    return pages


def _table_to_text(item: TableItem, doc) -> str:
    """
    Converts a Docling TableItem into a Markdown table string, so table
    content ends up as searchable text instead of being silently dropped.
    """
    try:
        return item.export_to_markdown(doc=doc)
    except TypeError:
        try:
            return item.export_to_markdown()
        except Exception:
            return ""
    except Exception:
        return ""


def load_pdf_docling(path: Path) -> List[Dict]:
    converter = DocumentConverter()
    result = converter.convert(str(path))
    doc = result.document
    page_texts: Dict[int, List[str]] = {}

    for item, _level in doc.iterate_items():
        prov = getattr(item, "prov", None)
        page_no = prov[0].page_no if prov else None

        if isinstance(item, TableItem):
            table_text = _table_to_text(item, doc)
            if table_text.strip():
                page_texts.setdefault(page_no, []).append(table_text)
            continue

        text = getattr(item, "text", None)
        if text and text.strip():
            page_texts.setdefault(page_no, []).append(text)

    pages = []
    for page_no, texts in sorted(
        page_texts.items(), key=lambda x: (x[0] is None, x[0])
    ):
        combined = "\n".join(texts)
        if combined.strip():
            pages.append(
                {"text": combined, "page_number": page_no, "source": path.name}
            )
    return pages


def load_docx(path: Path) -> List[Dict]:
    document = docx.Document(path)

    text = "\n".join(p.text for p in document.paragraphs if p.text.strip())

    if not text.strip():
        return []

    return [
        {
            "text": text,
            "page_number": None,
            "source": path.name,
        }
    ]


def load_txt(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")

    if not text.strip():
        return []

    return [
        {
            "text": text,
            "page_number": None,
            "source": path.name,
        }
    ]


def load_documents(data_dir: Path) -> List[Dict]:
    all_pages = []

    for path in sorted(data_dir.glob("*")):

        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            all_pages.extend(load_pdf_docling(path))

        elif suffix == ".docx":
            all_pages.extend(load_docx(path))

        elif suffix == ".txt":
            all_pages.extend(load_txt(path))

    return all_pages
