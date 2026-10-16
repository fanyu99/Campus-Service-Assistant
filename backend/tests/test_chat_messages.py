"""conversation_messages 读写与 GET /api/chat/messages（问题二）的测试。

覆盖修复方案 2.8：写入 / 读取顺序、归属隔离（他人标识 404）、空会话、
downgrade 后表不可用；另覆盖 GET 接口契约（一问一答成对、answer/sources 快照、
最近 200 条上限）。
"""

import json

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.pool import StaticPool

from app.models import AnswerStatus, Conversation, ConversationMessage
from app.schemas.chat import AnswerCard, ChatSource
from app.services.chat_messages import (
    MAX_HISTORY_MESSAGES,
    append_message,
    list_messages,
    recent_messages,
)
from app.services.llm_client import MockLLMClient

from tests.test_chat_api import OTHER_TOKEN, TOKEN, VALID_CARD, _document, _item, _post, _use_llm


def _conversation(db_session, conversation_id: str) -> Conversation:
    """直接造一条已归属 TOKEN 的会话（起止时间走列默认值）。"""
    conversation = Conversation(
        id=conversation_id,
        question="q",
        result_status=AnswerStatus.ANSWERED,
        session_token=TOKEN,
    )
    db_session.add(conversation)
    db_session.flush()
    return conversation


def _get(db_client: TestClient, conversation_id: str, token: str | None = TOKEN):
    headers = {"X-Session-Token": token} if token else {}
    return db_client.get(
        f"/api/chat/messages?conversation_id={conversation_id}", headers=headers
    )


# ── 服务层：写入与读取 ──────────────────────────────────────────────


def test_append_and_list_messages_in_order(db_session):
    _conversation(db_session, "c-1")

    append_message(db_session, "c-1", "question", "学生证丢了怎么补办？", AnswerStatus.ANSWERED)
    append_message(db_session, "c-1", "assistant", "提交补办申请。", AnswerStatus.ANSWERED)
    append_message(db_session, "c-1", "question", "需要照片吗？", AnswerStatus.ANSWERED)
    append_message(db_session, "c-1", "assistant", "需要。", AnswerStatus.ANSWERED)
    db_session.commit()

    items = list_messages(db_session, "c-1", TOKEN)
    assert [item.role for item in items] == [
        "question",
        "assistant",
        "question",
        "assistant",
    ]
    assert [item.content for item in items] == [
        "学生证丢了怎么补办？",
        "提交补办申请。",
        "需要照片吗？",
        "需要。",
    ]
    # 每条消息都带创建时间，前端按原样渲染
    assert all(item.created_at is not None for item in items)


def test_list_messages_ownership_isolation(db_session):
    _conversation(db_session, "c-2")
    append_message(db_session, "c-2", "question", "q", AnswerStatus.ANSWERED)
    db_session.commit()

    assert list_messages(db_session, "c-2", TOKEN) is not None
    # 他人标识 / 不带标识（会话已归属）都读不到
    assert list_messages(db_session, "c-2", OTHER_TOKEN) is None
    assert list_messages(db_session, "c-2", None) is None
    # 会话不存在
    assert list_messages(db_session, "not-exists", TOKEN) is None


def test_list_messages_empty_conversation_returns_empty_list(db_session):
    _conversation(db_session, "c-3")
    db_session.commit()
    # 存在且归属一致但无消息 → 空列表（区别于 None 的 404 语义）
    assert list_messages(db_session, "c-3", TOKEN) == []


def test_recent_messages_respects_limit(db_session):
    _conversation(db_session, "c-4")
    for index in range(12):
        append_message(db_session, "c-4", "question", f"问题{index}", AnswerStatus.ANSWERED)
    db_session.commit()

    # 倒序取尾部再翻转为时间正序：保留最后 5 条
    recent = recent_messages(db_session, "c-4", 5)
    assert [message.content for message in recent] == [
        "问题7",
        "问题8",
        "问题9",
        "问题10",
        "问题11",
    ]


def test_answer_and_sources_snapshot_roundtrip(db_session):
    _conversation(db_session, "c-5")
    append_message(
        db_session,
        "c-5",
        "assistant",
        "提交补办申请后按通知领取新证。",
        AnswerStatus.ANSWERED,
        answer=AnswerCard.model_validate(json.loads(VALID_CARD)),
        sources=[
            ChatSource(
                title="关于学生证补办工作的通知",
                department="学生工作处",
                published_at="2026-09-01",
                url="https://example.edu.cn/notice/001",
                item_code="S01",
                status="verified",
            )
        ],
    )
    db_session.commit()

    item = list_messages(db_session, "c-5", TOKEN)[0]
    assert item.answer is not None
    assert item.answer.title == "学生证补办"
    assert item.answer.steps == ["提交材料", "等待审核"]
    assert item.sources[0].title == "关于学生证补办工作的通知"
    assert item.sources[0].status == "verified"

    # 非 answered 轮不落卡片与来源快照
    append_message(db_session, "c-5", "assistant", "回复", AnswerStatus.UNSUPPORTED)
    db_session.commit()
    last = list_messages(db_session, "c-5", TOKEN)[-1]
    assert last.answer is None
    assert last.sources == []


def test_persisted_messages_are_cascade_deleted_with_conversation(db_session):
    _conversation(db_session, "c-6")
    append_message(db_session, "c-6", "question", "q", AnswerStatus.ANSWERED)
    db_session.commit()

    conversation = db_session.get(Conversation, "c-6")
    db_session.delete(conversation)
    db_session.commit()

    assert db_session.scalar(select(ConversationMessage)) is None


# ── 迁移：downgrade 后不可用 ────────────────────────────────────────


def test_messages_unavailable_after_downgrade(alembic_cfg):
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    connection = engine.connect()
    alembic_cfg.attributes["connection"] = connection
    try:
        command.upgrade(alembic_cfg, "head")
        assert "conversation_messages" in inspect(connection).get_table_names()

        command.downgrade(alembic_cfg, "0004")
        assert "conversation_messages" not in inspect(connection).get_table_names()

        # 表撤掉后：会话行仍在，但消息读写直接失败（功能随表消失，不静默降级）
        from app.db.session import create_session_factory

        session = create_session_factory(engine)()
        try:
            session.add(
                Conversation(
                    id="c-x",
                    question="q",
                    result_status=AnswerStatus.ANSWERED,
                    session_token=TOKEN,
                )
            )
            session.commit()
            with pytest.raises(Exception):
                list_messages(session, "c-x", TOKEN)
        finally:
            session.close()
    finally:
        connection.close()
        engine.dispose()


# ── 接口：GET /api/chat/messages ────────────────────────────────────


def test_get_messages_returns_rounds_in_order(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？").json()
    _post(db_client, "学生证补办需要准备照片吗？", conversation_id=first["conversation_id"])

    resp = _get(db_client, first["conversation_id"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert [m["role"] for m in body["messages"]] == [
        "question",
        "assistant",
        "question",
        "assistant",
    ]
    assert body["messages"][0]["content"] == "学生证丢了怎么补办？"
    # assistant 轮带回结构化卡片与来源快照（仍由 DB 映射，不采信模型输出）
    answered = body["messages"][1]
    assert answered["status"] == "answered"
    assert answered["answer"]["title"] == "学生证补办"
    assert answered["sources"][0]["title"] == "关于学生证补办工作的通知"
    assert answered["created_at"]


def test_get_messages_other_token_returns_404(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？").json()

    resp = _get(db_client, first["conversation_id"], token=OTHER_TOKEN)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_get_messages_without_token_returns_404_for_owned_conversation(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？").json()

    resp = _get(db_client, first["conversation_id"], token=None)
    assert resp.status_code == 404


def test_get_messages_unknown_conversation_returns_404(db_client):
    resp = _get(db_client, "not-exists")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_get_messages_smalltalk_round(db_client):
    """smalltalk 轮的消息：assistant 轮 content 即 text，无卡片。"""
    _use_llm(db_client, MockLLMClient())
    first = _post(db_client, "你好？").json()
    assert first["status"] == "smalltalk"

    resp = _get(db_client, first["conversation_id"])
    body = resp.json()
    assert body["total"] == 2
    assert body["messages"][1]["status"] == "smalltalk"
    assert body["messages"][1]["content"] == first["text"]
    assert body["messages"][1]["answer"] is None
    assert body["messages"][1]["sources"] == []


def test_get_messages_capped_at_200(db_client, db_session):
    """超过 200 条时只返回最近 200 条（时间正序）。"""
    _conversation(db_session, "c-cap")
    for index in range(MAX_HISTORY_MESSAGES + 5):
        append_message(db_session, "c-cap", "question", f"问题{index:04d}", AnswerStatus.ANSWERED)
    db_session.commit()

    body = _get(db_client, "c-cap").json()
    assert body["total"] == MAX_HISTORY_MESSAGES
    assert body["messages"][0]["content"] == "问题0005"
    assert body["messages"][-1]["content"] == f"问题{MAX_HISTORY_MESSAGES + 4:04d}"
