"""大模型客户端适配层。

当前实现：
- ``AgentArtsClient``（app.services.agentarts_client）：华为云 AgentArts（智果）
  问答工作流，配置 AGENTARTS_API_KEY + AGENTARTS_AGENT_ID 后优先使用，
  由工作流承担「意图 → 检索 → 判断 → 生成」全链路；
- ``MaaSClient``：华为云 MaaS（ModelArts Studio）模型服务——OpenAI 兼容协议：
    POST {base_url}/chat/completions
    Authorization: Bearer <API Key>
    {"model": "...", "messages": [{"role": "system"|"user", "content": "..."}]}
- ``MockLLMClient`` / ``UnavailableLLMClient``：本地替身与生产明确失败占位。

设计要点：
- 只依赖 ``LLMClient`` 协议，真实实现与替身实现可互换，编排层零改动；
- 传输层异常统一转成 LLMError 家族，由 api 层映射为契约错误码（见 fallback_service）。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Protocol, runtime_checkable

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 替身实现的缺省输出必须显式标注，避免被误当成真实模型结论
MOCK_STANDIN_NOTICE = "（本地替身实现，未接入模型服务，仅用于联调与测试）"
_ITEM_PATTERN = re.compile(r"【事项】(.+)")


class LLMError(Exception):
    """大模型调用异常基类。"""


class LLMTimeoutError(LLMError):
    """连接或读取超时（契约：UPSTREAM_TIMEOUT / 503）。"""


class LLMUpstreamError(LLMError):
    """上游返回异常：HTTP 错误、连接失败、结构异常等（契约：UPSTREAM_ERROR / 503）。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class MaaSClient:
    """华为云 MaaS 客户端（OpenAI 兼容）。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        connect_timeout: float = 2.0,
        read_timeout: float = 6.0,
        max_tokens: int = 1024,
    ) -> None:
        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        if not self._api_key:
            raise LLMUpstreamError("未配置 MaaS API Key")
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": self._max_tokens,
            "temperature": 0.2,
            "stream": False,
        }
        timeout = httpx.Timeout(self._read_timeout, connect=self._connect_timeout)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("模型服务响应超时") from exc
        except httpx.HTTPError as exc:
            raise LLMUpstreamError("模型服务不可达") from exc

        if response.status_code >= 400:
            raise LLMUpstreamError(
                f"模型服务返回 {response.status_code}", status_code=response.status_code
            )
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMUpstreamError("模型服务返回结构异常") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMUpstreamError("模型服务返回空内容")
        return content


class MockLLMClient:
    """替身实现：本地开发无密钥时兜底，也是测试注入用的确定性桩。

    - ``error`` 不为空时直接抛出，用于验证超时/上游异常的错误映射；
    - ``responses`` 按关键词命中返回，用于验证六态分支；
    - 都未命中时返回 ``default``；``default`` 为 None 时返回**显式标注的替身卡片**
      （事项名取自提示词，正文为空），避免出现「问转专业却答学生证」这类假答案。
    """

    def __init__(
        self,
        *,
        default: str | None = None,
        responses: dict[str, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._default = default
        self._responses = responses or {}
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self._error is not None:
            raise self._error
        for keyword, response in self._responses.items():
            if keyword in user:
                return response
        if self._default is not None:
            return self._default
        return self._placeholder(user)

    @staticmethod
    def _placeholder(user: str) -> str:
        match = _ITEM_PATTERN.search(user)
        title = match.group(1).strip() if match else "校园办事咨询"
        return json.dumps(
            {
                "title": title,
                "summary": f"{MOCK_STANDIN_NOTICE}未接入模型服务，无法给出正式办理说明。",
                "eligibility": [],
                "materials": [],
                "steps": [],
                "location": None,
                "deadline": None,
                "contacts": [],
                "warnings": [MOCK_STANDIN_NOTICE],
            },
            ensure_ascii=False,
        )


class UnavailableLLMClient:
    """生产环境未配置模型服务时的占位实现：明确失败，绝不编造答案。

    ``complete`` 抛 LLMUpstreamError，由 api 层映射为 503 UPSTREAM_ERROR。
    """

    def __init__(self, reason: str = "未配置模型服务") -> None:
        self._reason = reason

    def complete(self, system: str, user: str) -> str:
        raise LLMUpstreamError(self._reason)


def get_llm_client() -> LLMClient:
    """依赖注入入口，按优先级分流：
    1. 配置了 AgentArts（api_key + agent_id）→ AgentArts 工作流（项目目标形态）；
    2. 配置了 MaaS Key → MaaSClient 直连模型；
    3. 本地环境 → 替身实现（仅联调用）；
    4. 生产环境均未配置 → 明确失败（503）。

    保持无参签名，便于直接作为 FastAPI 依赖使用；测试用
    ``dependency_overrides[get_llm_client]`` 注入确定性替身。
    """
    settings = get_settings()
    if settings.agentarts_api_key.strip() and settings.agentarts_agent_id.strip():
        # 延迟导入：agentarts_client 依赖本模块的异常类型，避免循环导入
        from app.services.agentarts_client import AgentArtsClient

        return AgentArtsClient(
            api_key=settings.agentarts_api_key,
            agent_id=settings.agentarts_agent_id,
            base_url=settings.agentarts_base_url,
            connect_timeout=settings.agentarts_connect_timeout,
            read_timeout=settings.agentarts_read_timeout,
            max_attempts=settings.agentarts_max_attempts,
        )
    if settings.maas_api_key.strip():
        return MaaSClient(
            api_key=settings.maas_api_key,
            base_url=settings.maas_base_url,
            model=settings.maas_model,
            connect_timeout=settings.maas_connect_timeout,
            read_timeout=settings.maas_read_timeout,
            max_tokens=settings.maas_max_tokens,
        )
    if settings.app_env == "local":
        logger.warning(
            "未配置 AGENTARTS_API_KEY / MAAS_API_KEY：问答链路使用本地替身实现，"
            "输出仅用于联调，不代表真实模型结果"
        )
        return MockLLMClient()
    logger.error("未配置模型服务且当前环境非 local：问答接口将返回 503")
    return UnavailableLLMClient("未配置模型服务（AGENTARTS_API_KEY / MAAS_API_KEY 为空）")
