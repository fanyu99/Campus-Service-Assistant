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
    # 华为云 AgentArts（智果）智能体平台：问答工作流调用
    # base_url / agent_id 以控制台该工作流「API 调用」页给出的值为准；
    # api_key 与 agent_id 均配置后，问答链路优先走工作流（见 get_llm_client）
    agentarts_api_key: str = ""
    agentarts_base_url: str = ""
    agentarts_agent_id: str = ""
    agentarts_connect_timeout: float = 2.0
    agentarts_read_timeout: float = 15.0
    # 超时/连接异常的重试次数上限（4xx 与 429 不重试）
    agentarts_max_attempts: int = 2
    # 华为云 MaaS（ModelArts Studio）模型服务：OpenAI 兼容接口
    # base_url / model 请以控制台该模型「调用说明」给出的值为准
    maas_api_key: str = ""
    maas_base_url: str = "https://api.modelarts-maas.com/v2"
    maas_model: str = "DeepSeek-V3"
    maas_connect_timeout: float = 2.0
    maas_read_timeout: float = 6.0
    maas_max_tokens: int = 1024
    # 问答限流（契约 §6.7、OWASP A04）：单标识在窗口内的最大请求数
    chat_rate_limit_requests: int = 10
    chat_rate_limit_window_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()