from rag.chunker import chunk_pages
from rag.models import DocumentPage


def test_chunk_pages_preserves_metadata() -> None:
    text = "Alpha beta gamma. " * 120
    chunks = chunk_pages(
        [DocumentPage(text=text, source="handbook.pdf", page=3)],
        chunk_size=120,
        chunk_overlap=20,
    )

    assert len(chunks) > 1
    assert chunks[0].source == "handbook.pdf"
    assert chunks[0].page == 3
    assert chunks[0].chunk_index == 0


def test_chunk_overlap_must_be_smaller_than_size() -> None:
    try:
        chunk_pages([DocumentPage(text="hello", source="a.txt")], chunk_size=10, chunk_overlap=10)
    except ValueError as error:
        assert "chunk_overlap" in str(error)
    else:
        raise AssertionError("Expected ValueError")
