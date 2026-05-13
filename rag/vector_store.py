from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from rag.models import Chunk, RetrievedChunk


class LocalVectorStore:
    def __init__(self, persist_dir: Path) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir = persist_dir
        self.metadata_path = persist_dir / "chunks.json"
        self.embeddings_path = persist_dir / "embeddings.npy"

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        existing_chunks, existing_embeddings = self._load()
        records_by_id = {record["id"]: record for record in existing_chunks}
        vector_by_id = {
            record["id"]: existing_embeddings[index]
            for index, record in enumerate(existing_chunks)
        }

        for chunk, embedding in zip(chunks, embeddings):
            records_by_id[chunk.id] = {
                "id": chunk.id,
                "text": chunk.text,
                "source": chunk.source,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
            }
            vector_by_id[chunk.id] = np.array(embedding, dtype=np.float32)

        ordered_records = list(records_by_id.values())
        ordered_vectors = np.vstack([vector_by_id[record["id"]] for record in ordered_records])
        self.metadata_path.write_text(json.dumps(ordered_records, indent=2), encoding="utf-8")
        np.save(self.embeddings_path, ordered_vectors)

    def query(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        records, embeddings = self._load()
        if not records:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        embedding_norms = np.linalg.norm(embeddings, axis=1)
        similarities = (embeddings @ query) / np.maximum(embedding_norms * query_norm, 1e-12)
        best_indexes = np.argsort(similarities)[::-1][:top_k]

        retrieved: list[RetrievedChunk] = []
        for index in best_indexes:
            record = records[int(index)]
            similarity = float(similarities[int(index)])
            retrieved.append(
                RetrievedChunk(
                    text=record["text"],
                    source=record["source"],
                    page=record["page"],
                    chunk_index=record["chunk_index"],
                    distance=1.0 - similarity,
                )
            )
        return retrieved

    def count(self) -> int:
        records, _ = self._load()
        return len(records)

    def _load(self) -> tuple[list[dict], np.ndarray]:
        if not self.metadata_path.exists() or not self.embeddings_path.exists():
            return [], np.empty((0, 0), dtype=np.float32)

        records = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        embeddings = np.load(self.embeddings_path)
        return records, embeddings
