import asyncio

import voyageai

from config import get_settings


class VoyageEmbeddings:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.voyage_model
        self.client = voyageai.Client(api_key=settings.voyage_api_key)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed, texts, "document")

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await asyncio.to_thread(self._embed, [text], "query")
        return embeddings[0]

    def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        result = self.client.embed(texts, model=self.model, input_type=input_type)
        return [list(vector) for vector in result.embeddings]
