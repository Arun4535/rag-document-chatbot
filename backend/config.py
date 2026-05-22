from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite:///./docsense.db"
    chroma_persist_dir: str = "./chroma_db"
    environment: str = "development"
    claude_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
