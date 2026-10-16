from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.core.rate_limit import (
    SlidingWindowLimiter,
    get_chat_limiter,
    rate_limit_key,
)
from app.core.sanitize import reject_sensitive_or_injected, sanitize_message
from app.db.session import get_db
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessagesResponse,
)
from app.services.chat_messages import list_messages
from app.services.chat_service import handle_chat_message
from app.services.fallback_service import RATE_LIMITED_MESSAGE, to_business_error
from app.services.llm_client import LLMClient, LLMError, get_llm_client

router = APIRouter(prefix="/api")


@router.post("/chat/messages", response_model=ChatMessageResponse)
def post_chat_message(
    payload: ChatMessageRequest,
    request: Request,
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    limiter: SlidingWindowLimiter = Depends(get_chat_limiter),
) -> ChatMessageResponse:
    # 1) 限流先于一切下游调用：避免 LLM / 智能体成本被放大（契约 §6.7）
    if not limiter.allow(rate_limit_key(request, x_session_token)):
        raise BusinessError(429, "RATE_LIMITED", RATE_LIMITED_MESSAGE)

    # 2) 输入清洗与硬校验：敏感数据取值、提示词注入一律拒绝（契约 §6.6）
    message = sanitize_message(payload.message)
    reject_sensitive_or_injected(message)
    payload = payload.model_copy(update={"message": message})

    try:
        return handle_chat_message(db, payload, x_session_token, llm)
    except LLMError as exc:
        # 传输层失败转成契约错误码；输出不可用的降级在编排层内完成
        raise to_business_error(exc) from exc


@router.get("/chat/messages", response_model=ChatMessagesResponse)
def get_chat_messages(
    conversation_id: Annotated[str, Query(min_length=1)],
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
    db: Session = Depends(get_db),
) -> ChatMessagesResponse:
    """按会话读取消息明细（v1.3 新增）：历史可查看、可续接。

    归属校验与 POST 一致：会话不存在、或不属于当前匿名标识
    → 404 ``CONVERSATION_NOT_FOUND``（契约 §4.4 匿名隔离）。
    该会话存在但尚无消息时返回 200 + 空列表（如升级前创建的旧会话）。
    """
    items = list_messages(db, conversation_id, x_session_token)
    if items is None:
        raise BusinessError(404, "CONVERSATION_NOT_FOUND", "会话不存在或已过期")
    return ChatMessagesResponse(messages=items, total=len(items))
