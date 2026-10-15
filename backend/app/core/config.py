from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_port: int = 8000
    app_env: Literal["local", "production"] = "local"
    database_url: str = "mysql+pymysql://app:app@db:3306/campus"
    agentarts_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()