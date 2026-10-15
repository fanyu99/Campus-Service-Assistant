from pydantic import BaseModel, Field

from app.models.feedback import FeedbackReasonCode


class FeedbackRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    helpful: bool
    reason_code: FeedbackReasonCode | None = None
    comment: str | None = Field(default=None, max_length=200)


class FeedbackResponse(BaseModel):
    status: str = "ok"