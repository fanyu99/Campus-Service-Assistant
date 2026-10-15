from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Conversation
from app.schemas.conversation import ConversationListResponse, ConversationSummaryResponse


def list_conversations(
    session: Session, session_token: str | None, limit: int
) -> ConversationListResponse:
    token = session_token.strip() if session_token else ""
    if not token:
        return ConversationListResponse(conversations=[], total=0)
    condition = Conversation.session_token == token
    total = session.scalar(select(func.count()).select_from(Conversation).where(condition))
    rows = session.scalars(
        select(Conversation)
        .where(condition)
        .order_by(Conversation.last_message_at.desc())
        .limit(limit)
    ).all()
    summaries = [ConversationSummaryResponse.model_validate(row) for row in rows]
    return ConversationListResponse(conversations=summaries, total=total)