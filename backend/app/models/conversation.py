import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, enum_values, utc_now


class AnswerStatus(str, enum.Enum):
    ANSWERED = "answered"
    NEED_CLARIFICATION = "need_clarification"
    UNSUPPORTED = "unsupported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICT = "conflict"
    SERVICE_ERROR = "service_error"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "result_status IN ('answered', 'need_clarification', 'unsupported', "
            "'insufficient_evidence', 'conflict', 'service_error')",
            name="result_status_values",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question: Mapped[str] = mapped_column(Text)
    last_intent: Mapped[str | None] = mapped_column(
        ForeignKey("service_items.code", ondelete="RESTRICT"), nullable=True
    )
    result_status: Mapped[AnswerStatus] = mapped_column(
        Enum(AnswerStatus, values_callable=enum_values)
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    session_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="conversation")