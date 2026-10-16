"""问答链路的兜底与错误映射。

分流约定（与 docs/api.md §2.2 对齐）：
- 传输层失败（超时 / 上游异常）→ 503 + UPSTREAM_TIMEOUT / UPSTREAM_ERROR；
- 上游限流（MaaS 429）→ 429 + RATE_LIMITED；
- 模型可达但输出不可用 → 200 + status=service_error（前端展示重试提示，不白屏）。
任何路径都不编造答案，也不回传上游细节（密钥、主机名、堆栈）。
"""

from app.core.errors import BusinessError
from app.models import AnswerStatus
from app.schemas.chat import ChatMessageResponse
from app.services.llm_client import LLMError, LLMTimeoutError, LLMUpstreamError

UPSTREAM_TIMEOUT_MESSAGE = "智能问答服务响应超时，请稍后重试"
UPSTREAM_ERROR_MESSAGE = "智能问答服务暂时不可用，请稍后重试"
RATE_LIMITED_MESSAGE = "请求过于频繁，请稍后重试"

UPSTREAM_RATE_LIMIT_STATUS = 429


def to_business_error(exc: LLMError) -> BusinessError:
    if isinstance(exc, LLMTimeoutError):
        return BusinessError(503, "UPSTREAM_TIMEOUT", UPSTREAM_TIMEOUT_MESSAGE)
    if isinstance(exc, LLMUpstreamError) and exc.status_code == UPSTREAM_RATE_LIMIT_STATUS:
        return BusinessError(429, "RATE_LIMITED", RATE_LIMITED_MESSAGE)
    return BusinessError(503, "UPSTREAM_ERROR", UPSTREAM_ERROR_MESSAGE)


def service_error_response(
    conversation_id: str, intent: str | None = None
) -> ChatMessageResponse:
    """模型输出不可用时的降级响应：answer 恒为 null，来源为空。"""
    return ChatMessageResponse(
        conversation_id=conversation_id,
        status=AnswerStatus.SERVICE_ERROR,
        intent=intent,
        answer=None,
        sources=[],
        need_clarification=False,
        clarifying_question=None,
    )
