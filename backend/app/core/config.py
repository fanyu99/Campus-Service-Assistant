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
    # base_url / model 请以控制台该模型「调用说明」给出的值为准；
    # model 缺省取实测结论：同账号可用模型里 deepseek-v4-flash 延迟最稳
    # （20 次连续调用中位 4.75 秒 / p95 6.27 秒，全部 <8 秒），
    # 而 deepseek-v4.1-flash 虽能 20/20 正常作答，p95 却达 18.63 秒。
    maas_api_key: str = ""
    maas_base_url: str = "https://api.modelarts-maas.com/v2"
    maas_model: str = "deepseek-v4-flash"
    maas_connect_timeout: float = 2.0
    # 读超时留 7.5 秒：契约规定前端 8 秒超时（对应验收「典型回答 8 秒以内」），
    # 关闭思考链 + 简洁提示词 + deepseek-v4-flash 实测 p95 约 6.3 秒，7.5 秒留有余量。
    maas_read_timeout: float = 7.5
    maas_max_tokens: int = 1024
    # 关闭模型思考链：推理模型（如 deepseek-v4.1-flash）会先输出 reasoning_content，
    # 思考 token 既挤占 max_tokens 又显著拉长耗时（实测同一问题 12.8~65.5 秒），
    # 而契约要求典型回答 8 秒以内，故默认关闭。
    # 关闭写法以模型服务为准：当前模型支持 {"thinking": {"type": "disabled"}}。
    maas_disable_thinking: bool = True
    # 问答限流（契约 §6.7、OWASP A04）：单标识在窗口内的最大请求数
    chat_rate_limit_requests: int = 10
    chat_rate_limit_window_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()