from pathlib import Path
from typing import List, Dict
import pdfplumber
import docx
import tempfile
from io import BytesIO
import os
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import TableItem
from docling.datamodel.base_models import InputFormat
import concurrent.futures

from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

DOCUMENT_TIMEOUT_SECONDS = 180


def load_docx_docling_bytes(
    file_bytes: bytes,
    filename: str,
) -> List[Dict]:

    print(f"USING DOCLING FOR DOCX: {filename}")

    suffix = Path(filename).suffix.lower() or ".docx"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:

            temp_file.write(file_bytes)
            temp_path = temp_file.name

        converter = DocumentConverter()

        result = converter.convert(temp_path)

        document = result.document

        markdown_text = document.export_to_markdown()

        if not markdown_text or not markdown_text.strip():
            return []

        return [
            {
                "text": markdown_text.strip(),
                "page_number": None,
                "source": filename,
            }
        ]

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def load_pdf_pdfplumber_bytes(file_bytes: bytes, filename: str) -> List[Dict]:
    print("USING PDF_PLUMBER:_:_:_:_")
    pages = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            table_markdown_blocks = []
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue
                rows_markdown = []
                for row_idx, row in enumerate(table):
                    cells = [str(cell).strip() if cell else "" for cell in row]
                    rows_markdown.append("| " + " | ".join(cells) + " |")
                    if row_idx == 0:
                        rows_markdown.append("|" + "|".join(["---"] * len(cells)) + "|")
                table_markdown_blocks.append("\n".join(rows_markdown))

            combined_text = text
            if table_markdown_blocks:
                combined_text += "\n\n" + "\n\n".join(table_markdown_blocks)

            if combined_text.strip():
                pages.append(
                    {"text": combined_text, "page_number": i, "source": filename}
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
    print("USING DOCLING:_:_:_:_")

    suffix = Path(filename).suffix or ".pdf"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        converter = DocumentConverter()

        def _convert():
            result = converter.convert(tmp_path)
            return result.document

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_convert)
            try:
                doc = future.result(timeout=DOCUMENT_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(
                    f"Docling exceeded { DOCUMENT_TIMEOUT_SECONDS}s on '{filename}'"
                )

        return _extract_pages_from_docling_doc(doc, filename)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_pdf_from_bytes(file_bytes: bytes, filename: str) -> List[Dict]:
    try:
        return load_pdf_pdfplumber_bytes(file_bytes, filename)

    except Exception as e:
        return load_pdf_docling_bytes(file_bytes, filename)

        print(
            f"PdfPlumber failed/timed out on {filename} ({e}), falling back to pdfplumber."
        )


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


def load_documents_from_bytes(file_bytes: bytes, filename: str) -> List[Dict]:

    suffix = Path(filename).suffix

    if suffix == ".pdf":
        return load_pdf_from_bytes(file_bytes, filename)

    elif suffix == ".docx":
        return load_docx_docling_bytes(file_bytes, filename)

    elif suffix == ".txt":
        return load_txt_bytes(file_bytes, filename)

    else:
        raise ValueError(f"Unsupported file type:{suffix}")
