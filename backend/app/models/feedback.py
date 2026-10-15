import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, enum_values, utc_now


class FeedbackReasonCode(str, enum.Enum):
    SOURCE_ERROR = "SOURCE_ERROR"
    INCOMPLETE_STEPS = "INCOMPLETE_STEPS"
    OUTDATED_CONTENT = "OUTDATED_CONTENT"
    OTHER = "OTHER"


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "reason_code IS NULL OR reason_code IN "
            "('SOURCE_ERROR', 'INCOMPLETE_STEPS', 'OUTDATED_CONTENT', 'OTHER')",
            name="reason_code_values",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="RESTRICT"), index=True
    )
    helpful: Mapped[bool] = mapped_column(Boolean)
    reason_code: Mapped[FeedbackReasonCode | None] = mapped_column(
        Enum(FeedbackReasonCode, values_callable=enum_values), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation: Mapped["Conversation"] = relationship(back_populates="feedbacks")