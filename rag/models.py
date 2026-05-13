from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentPage:
    text: str
    source: str
    page: int | None = None


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    page: int | None
    chunk_index: int


@dataclass(frozen=True)
class IndexSummary:
    filename: str
    chunk_count: int


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    page: int | None
    chunk_index: int
    distance: float

    def citation_label(self, index: int) -> str:
        page = f", page {self.page}" if self.page is not None else ""
        return f"[{index}] {self.source}{page}, chunk {self.chunk_index}"


@dataclass(frozen=True)
class RAGResponse:
    answer: str
    sources: list[RetrievedChunk]
