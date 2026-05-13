from __future__ import annotations

from pathlib import Path

from rag.models import DocumentPage


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_document(path: Path) -> list[DocumentPage]:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    if extension == ".pdf":
        return load_pdf(path)
    if extension == ".docx":
        return load_docx(path)
    return load_txt(path)


def load_pdf(path: Path) -> list[DocumentPage]:
    import fitz

    pages: list[DocumentPage] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(DocumentPage(text=text, source=path.name, page=page_index))
    return pages


def load_docx(path: Path) -> list[DocumentPage]:
    from docx import Document

    document = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    text = "\n".join(paragraph for paragraph in paragraphs if paragraph)
    return [DocumentPage(text=text, source=path.name, page=None)] if text else []


def load_txt(path: Path) -> list[DocumentPage]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    return [DocumentPage(text=text, source=path.name, page=None)] if text else []
