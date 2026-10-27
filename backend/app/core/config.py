from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "TimAI Backend"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/timai"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/timai"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production"
    MASTER_ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef"


settings = Settings()
