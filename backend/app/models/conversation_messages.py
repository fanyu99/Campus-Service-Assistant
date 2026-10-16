"""会话消息明细（对话建模，问题二）。

``conversations`` 是「一行 = 一个问题」的单轮摘要（``question`` 为单数字段），
AI 的回答从未落库，导致历史无内容可展示、续接丢失上下文。本表按一问一答成对
落库，支撑三件事：

- 历史可查：``GET /api/chat/messages`` 按会话返回全部问答（迁移 0005）；
- 历史可续：后续轮次沿用同一 ``conversation_id``，提示词注入最近 N 轮；
- 上下文可用：生成提示词的【对话历史】段取自本表。

``answer_json`` / ``sources_json`` 只在 assistant 轮携带；``sources`` 仍由数据库
映射生成，不采信模型输出（契约 §1.2）。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, monotonic_utc_now
from app.models.conversation import Conversation

ROLE_QUESTION = "question"
ROLE_ASSISTANT = "assistant"


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        # 按会话 + 时间取「最近 N 轮」与「最近 200 条」都走这个索引
        Index(
            "ix_conversation_messages_conversation_id",
            "conversation_id",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    answer_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 单调时钟：同一事务内连续落库的消息（问 + 答）时间戳必须严格递增，
    # 否则按 created_at 排序不稳定（Windows 时钟粒度约 15.6ms）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=monotonic_utc_now
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
