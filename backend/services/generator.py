from anthropic import AsyncAnthropic

from config import get_settings


SYSTEM_PROMPT = """You are a document assistant. Answer using ONLY the provided context.
If the answer isn't in the context, say so clearly.
Be concise and precise. Always indicate which source you used."""


class ClaudeGenerator:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.claude_model
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def answer(self, question: str, chunks: list[dict]) -> str:
        context = build_context(chunks)
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=900,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer with citations.",
                }
            ],
        )
        return "".join(block.text for block in message.content if block.type == "text").strip()


def build_context(chunks: list[dict]) -> str:
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]
        page = metadata.get("page")
        page_text = "" if page in (None, -1) else f", page {page}"
        lines.append(f"[{index}] {metadata['filename']}{page_text}\n{chunk['text']}")
    return "\n\n".join(lines)
