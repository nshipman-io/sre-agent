"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    app_name: str = "SRE AI Agent"
    api_version: str = "v1"
    debug: bool = False

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"

    # Kubernetes Configuration
    k8s_config_path: str | None = None  # None means use in-cluster config
    k8s_namespace: str = "default"

    # ChromaDB Configuration
    chroma_persist_directory: str = "./data/chromadb"
    chroma_collection_name: str = "runbooks"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
