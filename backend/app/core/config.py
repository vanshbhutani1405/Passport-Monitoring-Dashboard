from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Passport Social Media Monitoring Platform"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/passport_monitor"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "passport-monitor:v1.0"
    youtube_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    scheduler_enabled: bool = False
    pipeline_interval_minutes: int = 180
    youtube_max_results_per_keyword: int = 20
    analysis_batch_size: int = 50
    embedding_batch_size: int = 100
    clustering_limit: int | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
