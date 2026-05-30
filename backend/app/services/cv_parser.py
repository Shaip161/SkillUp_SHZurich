import io
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document


def parse_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def parse_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_cv(data: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(data)
    if ext in (".docx", ".doc"):
        return parse_docx(data)
    raise ValueError(f"Unsupported CV format: '{ext}'. Upload a PDF or DOCX file.")
