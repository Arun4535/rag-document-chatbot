from __future__ import annotations

from functools import lru_cache

from fastembed import TextEmbedding


class LocalEmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = list(self.model.embed(texts))
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        vector = next(self.model.query_embed(text))
        return vector.tolist()

    @property
    def model(self) -> TextEmbedding:
        return get_text_embedding(self.model_name)


@lru_cache(maxsize=2)
def get_text_embedding(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)
