"""会话消息明细的读写（问题二：单轮建模 → 对话建模）。

``conversations`` 表是「一行 = 一个问题」的单轮摘要，AI 的回答从未落库，
导致历史无内容可展示、续接丢上下文。本模块负责：

- ``append_message``：单条消息落库（不提交，由调用方在同一事务内提交，
  保证「会话 + 消息」要么全成要么全不成）；
- ``list_messages``：按会话读取（默认最近 200 条，时间正序），
  归属校验与 ``chat_service._resolve_conversation`` 同一口径，不一致返回 None；
- ``recent_messages``：供生成提示词取「最近 N 轮」的内部助手（不校验归属，
  调用方 ``chat_service`` 已完成鉴权）。

归属口径：读取路径只做严格匹配，不做 POST 那样的「认领」——
认领（session_token 为空的会话被首个带标识请求接管）只发生在写入路径，
避免 GET 产生副作用。空会话（存在且归属一致但无消息）返回空列表而非 None。
"""

import json
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnswerStatus, Conversation, ConversationMessage
from app.schemas.chat import AnswerCard, ChatMessageItem, ChatSource
from app.services.session_token import normalize_session_token

# 单次读取上限：避免一次拉全量（历史可续接的会话消息会持续增长）
MAX_HISTORY_MESSAGES = 200


def append_message(
    session: Session,
    conversation_id: str,
    role: str,
    content: str,
    status: AnswerStatus,
    answer: AnswerCard | None = None,
    sources: Sequence[ChatSource] = (),
) -> ConversationMessage:
    """写入一条消息（只 add 不提交，由调用方统一 commit）。

    answer / sources 仅 assistant 轮携带；question 轮留空。
    sources 仍由数据库映射生成，不采信模型输出（契约 §1.2）。
    """
    message = ConversationMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        status=status.value,
        answer_json=answer.model_dump_json() if answer is not None else None,
        sources_json=(
            json.dumps([source.model_dump() for source in sources], ensure_ascii=False)
            if sources
            else None
        ),
    )
    session.add(message)
    return message


def list_messages(
    session: Session, conversation_id: str, session_token: str | None
) -> list[ChatMessageItem] | None:
    """按会话读取消息明细（最近 ``MAX_HISTORY_MESSAGES`` 条，时间正序）。

    会话不存在、或 ``session_token`` 与请求标识不一致 → None（由路由转
    404 ``CONVERSATION_NOT_FOUND``）；存在且归属一致但无消息 → 空列表。
    """
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        return None
    if conversation.session_token != normalize_session_token(session_token):
        return None
    return [
        _to_item(message)
        for message in recent_messages(session, conversation_id, MAX_HISTORY_MESSAGES)
    ]


def recent_messages(
    session: Session, conversation_id: str, limit: int
) -> list[ConversationMessage]:
    """最近 ``limit`` 条消息，按时间正序返回。

    倒序取 + 反转：走 (conversation_id, created_at) 复合索引取尾部，
    比全量加载再切片省内存。``id`` 作同刻兜底排序，保证结果稳定。
    """
    rows = session.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(
            ConversationMessage.created_at.desc(),
            ConversationMessage.id.desc(),
        )
        .limit(limit)
    ).all()
    rows.reverse()
    return rows


def _to_item(message: ConversationMessage) -> ChatMessageItem:
    answer = (
        AnswerCard.model_validate(json.loads(message.answer_json))
        if message.answer_json
        else None
    )
    sources = (
        [ChatSource.model_validate(item) for item in json.loads(message.sources_json)]
        if message.sources_json
        else []
    )
    return ChatMessageItem(
        role="question" if message.role == "question" else "assistant",
        content=message.content,
        status=AnswerStatus(message.status),
        answer=answer,
        sources=sources,
        created_at=message.created_at,
    )
