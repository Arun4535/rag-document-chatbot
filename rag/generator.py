from __future__ import annotations

import os

from anthropic import Anthropic

from rag.models import RetrievedChunk


SYSTEM_PROMPT = """You are a careful RAG assistant.
Answer only from the provided document context.
If the context is not enough, say: "I don't know based on the uploaded documents."
Use concise language and include bracket citations like [1], [2] for factual claims."""


class ClaudeAnswerGenerator:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")

        context = build_context(chunks)
        user_prompt = f"""Document context:

{context}

Question: {question}

Answer with citations. Do not use outside knowledge."""

        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        parts = []
        for block in message.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()


def build_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant document chunks were retrieved."

    lines = []
    for index, chunk in enumerate(chunks, start=1):
        citation = chunk.citation_label(index)
        lines.append(f"{citation}\n{chunk.text}")
    return "\n\n".join(lines)
