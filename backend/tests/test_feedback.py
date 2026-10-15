from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import AnswerStatus, Conversation, Feedback, ServiceItem

TOKEN_A = "aaaaaaaa-0000-0000-0000-00000000000a"


def _ensure_item(db_session, code):
    item = db_session.scalar(select(ServiceItem).where(ServiceItem.code == code))
    if item is None:
        db_session.add(
            ServiceItem(code=code, name="测试事项", category="测试", description="d")
        )
        db_session.commit()


def _add_conversation(db_session, question, result_status, token=TOKEN_A):
    _ensure_item(db_session, "S01")
    conv = Conversation(
        question=question,
        result_status=result_status,
        last_intent="S01",
        session_token=token,
    )
    db_session.add(conv)
    db_session.commit()
    return conv


def test_feedback_success_and_persisted(db_client: TestClient, db_session):
    conv = _add_conversation(db_session, "问题", AnswerStatus.ANSWERED)
    resp = db_client.post(
        "/api/feedback",
        json={
            "conversation_id": conv.id,
            "helpful": False,
            "reason_code": "OUTDATED_CONTENT",
            "comment": "办理地点似乎已经发生变化",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    db_session.expire_all()
    records = db_session.scalars(select(Feedback)).all()
    assert len(records) == 1
    record = records[0]
    assert record.conversation_id == conv.id
    assert record.helpful is False
    assert record.reason_code.value == "OUTDATED_CONTENT"
    assert record.comment == "办理地点似乎已经发生变化"
    assert record.created_at is not None


def test_feedback_repeat_appends_independent_records(db_client: TestClient, db_session):
    conv = _add_conversation(db_session, "问题", AnswerStatus.ANSWERED)
    for _ in range(2):
        resp = db_client.post(
            "/api/feedback",
            json={"conversation_id": conv.id, "helpful": True},
        )
        assert resp.status_code == 200
    db_session.expire_all()
    records = db_session.scalars(select(Feedback)).all()
    assert len(records) == 2
    assert records[0].id != records[1].id


def test_feedback_missing_required_fields_rejected(db_client: TestClient):
    for payload in (
        {"helpful": True},
        {"conversation_id": "x"},
    ):
        resp = db_client.post("/api/feedback", json=payload)
        assert resp.status_code == 422


def test_feedback_invalid_reason_code_rejected(db_client: TestClient):
    resp = db_client.post(
        "/api/feedback",
        json={"conversation_id": "x", "helpful": False, "reason_code": "BOGUS"},
    )
    assert resp.status_code == 422


def test_feedback_comment_too_long_rejected(db_client: TestClient):
    resp = db_client.post(
        "/api/feedback",
        json={"conversation_id": "x", "helpful": False, "comment": "字" * 201},
    )
    assert resp.status_code == 422


def test_feedback_reason_code_default_stored_as_null(db_client: TestClient, db_session):
    conv = _add_conversation(db_session, "问题", AnswerStatus.ANSWERED)
    resp = db_client.post(
        "/api/feedback",
        json={"conversation_id": conv.id, "helpful": True},
    )
    assert resp.status_code == 200
    db_session.expire_all()
    record = db_session.scalars(select(Feedback)).one()
    assert record.reason_code is None


def test_feedback_conversation_not_found(db_client: TestClient, db_session):
    resp = db_client.post(
        "/api/feedback",
        json={"conversation_id": "not-exists", "helpful": True},
    )
    assert resp.status_code == 404
    assert resp.json() == {
        "error": {"code": "CONVERSATION_NOT_FOUND", "message": "会话不存在或已过期"}
    }
    count = db_session.scalar(select(func.count()).select_from(Feedback))
    assert count == 0
