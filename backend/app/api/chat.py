from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.core.rate_limit import (
    SlidingWindowLimiter,
    get_chat_limiter,
    rate_limit_key,
)
from app.core.sanitize import reject_sensitive_or_injected, sanitize_message
from app.db.session import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
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
