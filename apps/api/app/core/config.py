from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./always_near.db"
    backend_cors_origins: list[AnyHttpUrl | str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    jwt_secret: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    password_bcrypt_rounds: int = Field(default=12, ge=4, le=31)
    log_level: str = "info"
    storage_provider: str = "local"
    storage_bucket: str | None = None
    storage_region: str | None = None
    storage_endpoint_url: str | None = None
    storage_access_key_id: str | None = None
    storage_secret_access_key: str | None = None
    storage_local_path: str = "./storage"
    signed_url_expire_seconds: int = 900
    voice_provider: str = "local"
    elevenlabs_api_key: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    heygen_liveavatar_api_key: str | None = None
    heygen_liveavatar_base_url: str = "https://api.heygen.com"
    heygen_liveavatar_enabled: bool = False

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str] | str:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
