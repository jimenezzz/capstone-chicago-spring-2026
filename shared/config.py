from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = Field(default="local", alias="ENV")
    database_url: str = Field(alias="DATABASE_URL")
    openfda_api_key: str | None = Field(default=None, alias="OPENFDA_API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    auth_secret_key: str = Field(default="local-dev-auth-secret-change-me", alias="AUTH_SECRET_KEY")
    auth_token_ttl_minutes: int = Field(default=60, alias="AUTH_TOKEN_TTL_MINUTES")
    auth_seed_default_users: bool = Field(default=True, alias="AUTH_SEED_DEFAULT_USERS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
