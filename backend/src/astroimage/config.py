from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "astroimage"
    environment: str = "development"
    log_level: str = "info"
    database_url: str = Field(min_length=1)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    otlp_endpoint: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
