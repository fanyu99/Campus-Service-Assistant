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
    # 华为云 MaaS（ModelArts Studio）模型服务：OpenAI 兼容接口
    # base_url / model 请以控制台该模型「调用说明」给出的值为准
    maas_api_key: str = ""
    maas_base_url: str = "https://api.modelarts-maas.com/v2"
    maas_model: str = "DeepSeek-V3"
    maas_connect_timeout: float = 2.0
    maas_read_timeout: float = 6.0
    maas_max_tokens: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()