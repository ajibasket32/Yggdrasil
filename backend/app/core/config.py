from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    log_level: str = "INFO"
    service_name: str = "yggdrasil-backend"
    database_url: SecretStr = SecretStr(
        "postgresql://yggdrasil:local_development_only@localhost:5432/yggdrasil"
    )
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"
    rag_embedding_dimensions: int = Field(default=256, ge=16, le=512)
    rag_cache_ttl_seconds: int = Field(default=300, ge=1, le=3600)
    rag_index_max_attempts: int = Field(default=5, ge=1, le=20)
    rag_qdrant_timeout_seconds: float = Field(default=5, gt=0, le=30)
    worker_heartbeat_ttl_seconds: int = Field(default=45, ge=15, le=300)

    ai_provider_order: str = "gemini,groq,openai,anthropic,openrouter,ollama,cached"
    ai_cloud_timeout_seconds: float = Field(default=10, gt=0, le=10)
    ai_local_timeout_seconds: float = Field(default=30, gt=0, le=30)
    ai_provider_attempts: int = Field(default=2, ge=1, le=3)
    ai_requests_per_minute: int = Field(default=20, ge=1)
    ai_requests_per_hour: int = Field(default=200, ge=1)
    ai_max_output_tokens: int = Field(default=1000, ge=1, le=1000)

    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = ""
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_model: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_model: str = ""

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the configured PostgreSQL URL with SQLAlchemy's async driver."""
        url = self.database_url.get_secret_value()
        if url.startswith("postgresql+asyncpg://"):
            return url
        return url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    @property
    def provider_order(self) -> tuple[str, ...]:
        """Return normalized configured provider names."""
        return tuple(
            provider.strip().lower()
            for provider in self.ai_provider_order.split(",")
            if provider.strip()
        )


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per process."""
    return Settings()
