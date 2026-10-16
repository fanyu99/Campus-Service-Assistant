"""华为云 AgentArts（智果）智能体平台：问答工作流客户端。

职责（实施方案第 4/5 周）：调用已在 AgentArts 控制台发布的工作流，
由工作流承担「意图识别 → 知识检索 → 依据判断 → 大模型生成」全链路
（节点配置见 docs/AgentArts工作流配置说明.md），后端只负责调用、
校验、持久化与来源展示。

设计要点（与 MaaSClient 保持一致）：
- 只依赖 ``LLMClient`` 协议：``complete(system, user) -> str``，
  编排层（chat_service）零改动，路由由 ``get_llm_client`` 统一分流；
- 调用地址、工作流 ID 均可配置，endpoint 与 payload 以控制台该工作流
  「API 调用」页给出的值为准，本实现按常见形态组织并做了容错解析；
- 传输层异常统一转成 LLMError 家族（LLMTimeoutError / LLMUpstreamError），
  由 api 层映射为契约错误码（UPSTREAM_TIMEOUT / UPSTREAM_ERROR / RATE_LIMITED）；
- 超时与连接异常按 ``max_attempts`` 重试；4xx 与 429 不重试（限流直接抛出）。
"""

from __future__ import annotations

import logging

import httpx

from app.services.llm_client import (
    LLMTimeoutError,
    LLMUpstreamError,
)

logger = logging.getLogger(__name__)

# 调用地址缺省为空：必须配置 AGENTARTS_BASE_URL（控制台「API 调用」页给出）
DEFAULT_CONNECT_TIMEOUT = 2.0
DEFAULT_READ_TIMEOUT = 15.0
DEFAULT_MAX_ATTEMPTS = 2

# 工作流输出文本的候选提取器（按优先级尝试，覆盖常见返回结构）
_OUTPUT_EXTRACTORS: tuple = (
    lambda data: data["output"]["text"],
    lambda data: data["data"]["output"]["text"],
    lambda data: data["data"]["output"],
    lambda data: data["output"],
    lambda data: data["answer"],
    lambda data: data["content"],
    lambda data: data["choices"][0]["message"]["content"],
)


class AgentArtsClient:
    """AgentArts 工作流客户端（OpenAI 风格之外的智能体调用形态）。"""

    def __init__(
        self,
        *,
        api_key: str,
        agent_id: str,
        base_url: str,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        self._api_key = api_key.strip()
        self._agent_id = agent_id.strip()
        self._base_url = base_url.strip().rstrip("/")
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_attempts = max(1, max_attempts)

    def complete(self, system: str, user: str) -> str:
        if not self._api_key:
            raise LLMUpstreamError("未配置 AgentArts API Key")
        if not self._agent_id:
            raise LLMUpstreamError("未配置 AgentArts 工作流 ID")
        if not self._base_url:
            raise LLMUpstreamError("未配置 AgentArts 调用地址")

        payload = {
            "agent_id": self._agent_id,
            "inputs": {"question": user, "system_prompt": system},
            "stream": False,
        }
        timeout = httpx.Timeout(self._read_timeout, connect=self._connect_timeout)
        last_error: LLMTimeoutError | LLMUpstreamError | None = None

        for attempt in range(1, self._max_attempts + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        self._base_url,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                    )
            except httpx.TimeoutException as exc:
                last_error = LLMTimeoutError("智能体工作流响应超时")
                logger.warning("AgentArts 工作流超时（第 %d 次尝试）", attempt)
                continue
            except httpx.HTTPError as exc:
                last_error = LLMUpstreamError("智能体工作流不可达")
                logger.warning("AgentArts 工作流连接失败（第 %d 次尝试）", attempt)
                continue

            if response.status_code == 429:
                raise LLMUpstreamError("智能体工作流限流", status_code=429)
            if response.status_code >= 400:
                raise LLMUpstreamError(
                    f"智能体工作流返回 {response.status_code}",
                    status_code=response.status_code,
                )
            return self._extract_content(response)

        raise last_error or LLMUpstreamError("智能体工作流调用失败")

    @staticmethod
    def _extract_content(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError as exc:
            raise LLMUpstreamError("智能体工作流返回结构异常") from exc
        for extractor in _OUTPUT_EXTRACTORS:
            try:
                value = extractor(data)
            except (KeyError, IndexError, TypeError):
                continue
            if isinstance(value, str) and value.strip():
                return value
        raise LLMUpstreamError("智能体工作流未返回有效输出")
