from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.models import Conversation, Feedback
from app.schemas.feedback import FeedbackRequest


def submit_feedback(session: Session, payload: FeedbackRequest) -> None:
    conversation = session.scalar(
        select(Conversation).where(Conversation.id == payload.conversation_id)
    )
    if conversation is None:
        raise BusinessError(404, "CONVERSATION_NOT_FOUND", "会话不存在或已过期")
    feedback = Feedback(
        conversation_id=payload.conversation_id,
        helpful=payload.helpful,
        reason_code=payload.reason_code,
        comment=payload.comment,
    )
    session.add(feedback)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise