from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class AppConfig:
    upload_dir: Path
    vector_store_dir: Path
    embedding_model: str
    anthropic_model: str
    top_k: int
    chunk_size: int
    chunk_overlap: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            upload_dir=Path(os.getenv("UPLOAD_DIR", PROJECT_ROOT / "data" / "uploads")),
            vector_store_dir=Path(os.getenv("VECTOR_STORE_DIR", PROJECT_ROOT / "data" / "vector_store")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-1-20250805"),
            top_k=int(os.getenv("TOP_K", "4")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
        )
