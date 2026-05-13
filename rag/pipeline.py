from __future__ import annotations

from pathlib import Path

from rag.chunker import chunk_pages
from rag.config import AppConfig
from rag.embeddings import LocalEmbeddingModel
from rag.generator import ClaudeAnswerGenerator
from rag.loader import load_document
from rag.models import IndexSummary, RAGResponse
from rag.vector_store import LocalVectorStore


class RAGPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.embeddings = LocalEmbeddingModel(config.embedding_model)
        self.vector_store = LocalVectorStore(config.vector_store_dir)
        self.generator = ClaudeAnswerGenerator(config.anthropic_model)

    def index_document(self, path: Path) -> IndexSummary:
        pages = load_document(path)
        chunks = chunk_pages(
            pages,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        vectors = self.embeddings.embed_documents([chunk.text for chunk in chunks])
        self.vector_store.add_chunks(chunks, vectors)
        return IndexSummary(filename=path.name, chunk_count=len(chunks))

    def answer(self, question: str) -> RAGResponse:
        query_vector = self.embeddings.embed_query(question)
        chunks = self.vector_store.query(query_vector, self.config.top_k)
        answer = self.generator.generate(question, chunks)
        return RAGResponse(answer=answer, sources=chunks)
