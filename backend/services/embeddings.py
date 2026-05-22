import asyncio

from fastembed import TextEmbedding

from config import get_settings


class FastEmbedEmbeddings:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model
        self.model = TextEmbedding(model_name=self.model_name)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_documents, texts)

    async def embed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_query, text)

    def _embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.model.embed(texts)]

    def _embed_query(self, text: str) -> list[float]:
        return next(self.model.query_embed(text)).tolist()
