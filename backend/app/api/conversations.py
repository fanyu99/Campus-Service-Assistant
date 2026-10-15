from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import ConversationListResponse
from app.services.conversations import list_conversations

router = APIRouter(prefix="/api")


@router.get("/conversations", response_model=ConversationListResponse)
def get_conversations(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    return list_conversations(db, x_session_token, limit)