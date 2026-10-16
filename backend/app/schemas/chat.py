import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.conversation import AnswerStatus

MAX_MESSAGE_LENGTH = 200

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ChatContext(BaseModel):
    """检索范围提示（选填）：校区与学生类型，用于缩小知识检索范围。"""

    campus: str | None = None
    student_type: str | None = None


class ChatMessageRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1)
    context: ChatContext | None = None

    @field_validator("message")
    @classmethod
    def _reject_blank_message(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("message 不能为空")
        return text


class AnswerCard(BaseModel):
    """契约 §3.3 的结构化办事卡片（仅 answered 状态下返回）。"""

    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    eligibility: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    location: str | None = None
    deadline: str | None = None
    contacts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("deadline")
    @classmethod
    def _normalize_deadline(cls, value: str | None) -> str | None:
        """契约要求 YYYY-MM-DD；模型给出其它格式时按「无截止日期」处理，不整卡失败。"""
        if value is None:
            return None
        text = value.strip()
        return text if _DATE_PATTERN.match(text) else None


class ChatSource(BaseModel):
    """契约 §3.2 的来源条目，由后端从 source_documents 映射，不采信模型输出。"""

    title: str
    department: str
    published_at: str
    url: str
    item_code: str | None = None
    status: str | None = None


class ChatMessageResponse(BaseModel):
    """契约 §4.3 的响应结构。非 answered 时 answer 恒为 null（显式返回）。"""

    conversation_id: str
    status: AnswerStatus
    intent: str | None
    answer: AnswerCard | None
    sources: list[ChatSource]
    need_clarification: bool
    clarifying_question: str | None


class ChatOutcomeKind(BaseModel):
    """内部使用的模型输出解析结果标记（不对外暴露）。"""

    kind: Literal["card", "insufficient", "invalid"]
