import re

from rank_bm25 import BM25Okapi

from services.vectorstore import ChromaStore


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class HybridRetriever:
    def __init__(self, store: ChromaStore) -> None:
        self.store = store

    async def retrieve(self, doc_id: str, question: str, query_embedding: list[float]) -> list[dict]:
        semantic = await self.store.semantic_search(doc_id, query_embedding, limit=7)
        keyword = await self._keyword_search(doc_id, question, limit=7)
        return reciprocal_rank_fusion([semantic, keyword], limit=5)

    async def _keyword_search(self, doc_id: str, question: str, limit: int) -> list[dict]:
        chunks = await self.store.get_doc_chunks(doc_id)
        if not chunks:
            return []

        tokenized_corpus = [tokenize(chunk["text"]) for chunk in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenize(question))
        ranked_indexes = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)[:limit]

        ranked = []
        max_score = max(scores) if len(scores) else 0
        for idx in ranked_indexes:
            chunk = chunks[idx]
            # Normalize BM25 scores so the frontend can render them beside semantic scores.
            chunk["score"] = float(scores[idx] / max_score) if max_score else 0.0
            ranked.append(chunk)
        return ranked


def reciprocal_rank_fusion(result_sets: list[list[dict]], limit: int = 5, k: int = 60) -> list[dict]:
    fused: dict[str, dict] = {}

    for results in result_sets:
        for rank, item in enumerate(results, start=1):
            item_id = item["id"]
            if item_id not in fused:
                fused[item_id] = {**item, "rrf_score": 0.0}
            # RRF rewards chunks that appear in both semantic and keyword rankings,
            # making retrieval more robust than either method alone.
            fused[item_id]["rrf_score"] += 1.0 / (k + rank)

    ranked = sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)
    for item in ranked:
        item["score"] = float(item["rrf_score"])
    return ranked[:limit]
