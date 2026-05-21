from pathlib import Path
from uuid import uuid4

import chromadb

from config import get_settings
from services.chunker import TextChunk


class ChromaStore:
    def __init__(self) -> None:
        settings = get_settings()
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="docsense_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    async def add_chunks(
        self,
        doc_id: str,
        filename: str,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        if not chunks:
            return

        ids = [f"{doc_id}:{chunk.chunk_index}:{uuid4()}" for chunk in chunks]
        self.collection.add(
            ids=ids,
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "page": chunk.page if chunk.page is not None else -1,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    async def semantic_search(self, doc_id: str, embedding: list[float], limit: int = 7) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where={"doc_id": doc_id},
            include=["documents", "metadatas", "distances"],
        )
        return self._format_query_results(results)

    async def get_doc_chunks(self, doc_id: str) -> list[dict]:
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"],
        )
        chunks = []
        for idx, text in enumerate(results.get("documents", [])):
            metadata = results.get("metadatas", [])[idx]
            chunks.append(
                {
                    "text": text,
                    "metadata": metadata,
                    "score": 0.0,
                    "id": results.get("ids", [])[idx],
                }
            )
        return chunks

    def _format_query_results(self, results: dict) -> list[dict]:
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        formatted = []
        for idx, text in enumerate(docs):
            distance = float(distances[idx])
            formatted.append(
                {
                    "id": ids[idx],
                    "text": text,
                    "metadata": metadatas[idx],
                    "score": max(0.0, 1.0 - distance),
                }
            )
        return formatted
