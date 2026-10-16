from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import AnswerStatus, Conversation, ServiceItem

TOKEN_A = "aaaaaaaa-0000-0000-0000-00000000000a"
TOKEN_B = "bbbbbbbb-0000-0000-0000-00000000000b"
EXPECTED_ERROR_BODY = {
    "error": {"code": "INVALID_REQUEST", "message": "请求参数校验失败"}
}


def _ensure_item(db_session, code):
    item = db_session.scalar(select(ServiceItem).where(ServiceItem.code == code))
    if item is None:
        db_session.add(
            ServiceItem(code=code, name="测试事项", category="测试", description="d")
        )
        db_session.commit()


def _add_conversation(db_session, token, question, result_status, minutes, last_intent="S01"):
    if last_intent:
        _ensure_item(db_session, last_intent)
    moment = datetime(2026, 10, 1, 12, minutes, tzinfo=timezone.utc)
    conv = Conversation(
        question=question,
        result_status=result_status,
        last_intent=last_intent,
        started_at=moment,
        last_message_at=moment,
        session_token=token,
    )
    db_session.add(conv)
    db_session.commit()
    return conv


def test_conversations_isolation_between_tokens(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "A 的问题", AnswerStatus.ANSWERED, 1)
    _add_conversation(db_session, TOKEN_B, "B 的问题", AnswerStatus.ANSWERED, 2)
    resp = db_client.get(
        "/api/conversations", headers={"X-Session-Token": TOKEN_A}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert [c["question"] for c in body["conversations"]] == ["A 的问题"]
    assert all(c["question"] != "B 的问题" for c in body["conversations"])


def test_conversations_missing_token_short_circuit(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "A 的问题", AnswerStatus.ANSWERED, 1)
    resp = db_client.get("/api/conversations")
    assert resp.status_code == 200
    assert resp.json() == {"conversations": [], "total": 0}


def test_conversations_blank_token_short_circuit(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "A 的问题", AnswerStatus.ANSWERED, 1)
    for headers in ({"X-Session-Token": ""}, {"X-Session-Token": "   "}):
        resp = db_client.get("/api/conversations", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == {"conversations": [], "total": 0}


def test_conversations_limit_default_and_boundary(db_client: TestClient, db_session):
    for minutes in range(1, 6):
        _add_conversation(
            db_session, TOKEN_A, f"问题 {minutes}", AnswerStatus.ANSWERED, minutes
        )
    resp = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    assert resp.status_code == 200
    assert len(resp.json()["conversations"]) == 5
    assert resp.json()["total"] == 5


def test_conversations_limit_out_of_range_rejected(db_client: TestClient):
    for limit in ("0", "-1", "51"):
        resp = db_client.get(f"/api/conversations?limit={limit}")
        assert resp.status_code == 422
        assert resp.json() == EXPECTED_ERROR_BODY


def test_conversations_limit_non_integer_rejected(db_client: TestClient):
    resp = db_client.get("/api/conversations?limit=abc")
    assert resp.status_code == 422
    assert resp.json() == EXPECTED_ERROR_BODY


def test_conversations_sorted_by_last_message_desc(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "早的问题", AnswerStatus.ANSWERED, 1)
    _add_conversation(db_session, TOKEN_A, "晚的问题", AnswerStatus.ANSWERED, 5)
    _add_conversation(db_session, TOKEN_A, "中间的问题", AnswerStatus.ANSWERED, 3)
    resp = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    questions = [c["question"] for c in resp.json()["conversations"]]
    assert questions == ["晚的问题", "中间的问题", "早的问题"]


def test_conversations_summary_fields(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "问题", AnswerStatus.ANSWERED, 1)
    conv = _add_conversation(db_session, TOKEN_A, "无意图", AnswerStatus.UNSUPPORTED, 2, last_intent=None)
    conv.last_intent = None
    db_session.commit()
    resp = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    conversations = resp.json()["conversations"]
    assert len(conversations) == 2
    for item in conversations:
        assert set(item) == {
            "id",
            "question",
            "last_intent",
            "result_status",
            "started_at",
            "last_message_at",
        }
    by_question = {c["question"]: c for c in conversations}
    assert by_question["无意图"]["last_intent"] is None
    assert by_question["问题"]["result_status"] == "answered"


def test_conversations_time_iso8601_with_timezone(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "问题", AnswerStatus.ANSWERED, 1)
    resp = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    item = resp.json()["conversations"][0]
    assert item["started_at"].endswith(("Z", "+00:00"))
    assert item["last_message_at"].endswith(("Z", "+00:00"))


def test_conversations_readonly_idempotent(db_client: TestClient, db_session):
    _add_conversation(db_session, TOKEN_A, "问题", AnswerStatus.ANSWERED, 1)
    first = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    second = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN_A})
    assert first.json() == second.json()


def test_conversations_long_token_matches_truncated_write(db_client: TestClient, db_session):
    """写入与读取必须用同一套规范化规则，否则会话在「最近记录」中不可见。"""
    stored_token = "a" * 64
    _add_conversation(db_session, stored_token, "超长标识的问题", AnswerStatus.ANSWERED, 1)
    resp = db_client.get("/api/conversations", headers={"X-Session-Token": "a" * 80})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["conversations"][0]["question"] == "超长标识的问题"