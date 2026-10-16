from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import handle_chat_message
from app.services.fallback_service import to_business_error
from app.services.llm_client import LLMClient, LLMError, get_llm_client

router = APIRouter(prefix="/api")


@router.post("/chat/messages", response_model=ChatMessageResponse)
def post_chat_message(
    payload: ChatMessageRequest,
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> ChatMessageResponse:
    try:
        return handle_chat_message(db, payload, x_session_token, llm)
    except LLMError as exc:
        # 传输层失败转成契约错误码；输出不可用的降级在编排层内完成
        raise to_business_error(exc) from exc
