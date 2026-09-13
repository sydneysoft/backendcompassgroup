from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Bus Platform API"
    app_env: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+pysqlite:///./busapp.db"
    transport_provider: Literal["mock", "distribusion"] = "mock"
    distribusion_base_url: str | None = None
    distribusion_api_key: str | None = None
    payments_mode: Literal["sandbox", "production"] = "sandbox"
    admin_api_key: str = "change-me"
    cors_origins: str = Field(
        default=(
            "http://localhost:5173,http://localhost:3000,"
            "https://frontendcompassgroup.vercel.app,"
            "https://orangegroup.vercel.app"
        )
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
