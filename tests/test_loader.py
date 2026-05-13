from pathlib import Path

from rag.loader import load_document


def test_load_txt(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("Important project notes", encoding="utf-8")

    pages = load_document(path)

    assert len(pages) == 1
    assert pages[0].text == "Important project notes"
    assert pages[0].source == "notes.txt"
