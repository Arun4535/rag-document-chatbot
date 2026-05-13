from __future__ import annotations

import hashlib
import re

from rag.models import Chunk, DocumentPage


def chunk_pages(
    pages: list[DocumentPage],
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    for page in pages:
        normalized = normalize_text(page.text)
        start = 0
        page_chunk_index = 0

        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            if end < len(normalized):
                boundary = normalized.rfind(" ", start, end)
                if boundary > start + int(chunk_size * 0.6):
                    end = boundary

            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunk_id = stable_chunk_id(page.source, page.page, page_chunk_index, chunk_text)
                chunks.append(
                    Chunk(
                        id=chunk_id,
                        text=chunk_text,
                        source=page.source,
                        page=page.page,
                        chunk_index=page_chunk_index,
                    )
                )
                page_chunk_index += 1

            if end >= len(normalized):
                break
            start = max(end - chunk_overlap, 0)

    return chunks


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def stable_chunk_id(source: str, page: int | None, chunk_index: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    page_part = page if page is not None else "na"
    return f"{source}:{page_part}:{chunk_index}:{digest}"
