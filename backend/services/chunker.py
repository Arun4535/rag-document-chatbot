from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    page: int | None
    chunk_index: int


class RecursiveTextSplitter:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def split_pages(self, pages: list[tuple[str, int | None]]) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for text, page in pages:
            for chunk_text in self._split_text(text.strip()):
                if chunk_text:
                    chunks.append(TextChunk(text=chunk_text, page=page, chunk_index=len(chunks)))
        return chunks

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        separator = self._choose_separator(text)
        parts = list(text) if separator == "" else text.split(separator)
        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = part if not current else f"{current}{separator}{part}"
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current.strip())
                current = self._tail(current)

            if len(part) > self.chunk_size:
                chunks.extend(self._split_text(part))
                current = ""
            else:
                current = part

        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _choose_separator(self, text: str) -> str:
        for separator in self.separators:
            if separator and separator in text:
                return separator
        return ""

    def _tail(self, text: str) -> str:
        return text[-self.overlap :] if self.overlap else ""
