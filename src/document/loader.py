from pathlib import Path
from typing import List, Dict
import pdfplumber
import docx
import tempfile
from io import BytesIO
import os
from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem


# def load_pdf_pdfplumber(file_bytes: bytes, filename: str) -> List[Dict]:

#     pages = []

#     with pdfplumber.open(path) as pdf:
#         for i, page in enumerate(pdf.pages, start=1):
#             text = page.extract_text() or ""

#             if text.strip():
#                 pages.append(
#                     {
#                         "text": text,
#                         "page_number": i,
#                         "source": path.name,
#                     }
#                 )

#     return pages


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


def _extract_pages_from_docling_doc(doc, filename: str) -> List[Dict]:
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
            pages.append({"text": combined, "page_number": page_no, "source": filename})
    return pages


def load_pdf_docling_bytes(file_bytes: bytes, filename: str) -> List[Dict]:

    suffix = Path(filename).suffix or ".pdf"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        converter = DocumentConverter()
        result = converter.convert(tmp_path)
        doc = result.document

        return _extract_pages_from_docling_doc(doc, filename)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_docx_bytes(file_bytes: bytes, filename: str) -> List[Dict]:
    document = docx.Document(BytesIO(file_bytes))

    text = "\n".join(p.text for p in document.paragraphs if p.text.strip())

    if not text.strip():
        return []

    return [
        {
            "text": text,
            "page_number": None,
            "source": filename,
        }
    ]


def load_txt_bytes(file_bytes: bytes, filename: str) -> List[Dict]:
    text = file_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        return []

    return [
        {
            "text": text,
            "page_number": None,
            "source": filename,
        }
    ]


def load_documents_from_bytes(file_bytes:bytes,  filename:str) -> List[Dict]:
    
        suffix = Path(filename).suffix

        if suffix == ".pdf":
            return load_pdf_docling_bytes(file_bytes,filename)

        elif suffix == ".docx":
            return load_docx_bytes(file_bytes,filename)

        elif suffix == ".txt":
            return load_txt_bytes(file_bytes,filename)

        else:
            raise ValueError(f"Unsupported file type:{suffix}")
 


