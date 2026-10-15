from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import AnswerStatus
from app.schemas.common import UtcDateTime


class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    last_intent: str | None
    result_status: AnswerStatus
    started_at: UtcDateTime
    last_message_at: UtcDateTime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]
    total: int = Field(ge=0)