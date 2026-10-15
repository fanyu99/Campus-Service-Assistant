from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    AnswerStatus,
    Conversation,
    Feedback,
    ServiceItem,
    SourceDocument,
)


def _make_item(db_session, code="S01"):
    item = ServiceItem(
        code=code,
        name="学生证补办",
        category="证件",
        description="材料、流程与办理地点",
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_conversation(db_session, item):
    conv = Conversation(
        question="学生证丢了怎么补办？",
        result_status=AnswerStatus.ANSWERED,
        last_intent=item.code,
    )
    db_session.add(conv)
    db_session.flush()
    return conv


def test_service_items_columns(db_session):
    cols = {c.name for c in ServiceItem.__table__.columns}
    assert cols == {
        "id",
        "code",
        "name",
        "category",
        "description",
        "enabled",
        "created_at",
        "updated_at",
    }


def test_source_documents_columns(db_session):
    cols = {c.name for c in SourceDocument.__table__.columns}
    assert cols == {
        "id",
        "service_item_id",
        "title",
        "department",
        "official_url",
        "publish_date",
        "effective_from",
        "effective_to",
        "audience",
        "campus",
        "status",
        "version",
        "reviewed_at",
    }


def test_conversations_columns_whitelist(db_session):
    cols = {c.name for c in Conversation.__table__.columns}
    assert cols == {
        "id",
        "question",
        "last_intent",
        "result_status",
        "started_at",
        "last_message_at",
        "session_token",
    }
    banned = {
        "name",
        "real_name",
        "student_id",
        "student_number",
        "id_card",
        "id_number",
        "bank_card",
        "password",
        "phone",
        "username",
    }
    assert not cols & banned


def test_feedback_columns(db_session):
    cols = {c.name for c in Feedback.__table__.columns}
    assert cols == {
        "id",
        "conversation_id",
        "helpful",
        "reason_code",
        "comment",
        "created_at",
    }


def test_service_item_defaults(db_session):
    item = _make_item(db_session)
    assert item.enabled is True
    assert item.created_at is not None
    assert item.created_at.tzinfo is not None
    assert item.updated_at.tzinfo is not None
    db_session.rollback()


def test_conversation_id_auto_uuid(db_session):
    item = _make_item(db_session)
    conv = _make_conversation(db_session, item)
    assert len(conv.id) == 36
    assert conv.id.count("-") == 4
    assert conv.started_at.tzinfo is not None
    assert conv.last_message_at.tzinfo is not None
    db_session.rollback()


def test_service_item_code_unique_rejected(db_session):
    _make_item(db_session, code="S01")
    with pytest.raises(IntegrityError):
        _make_item(db_session, code="S01")
    db_session.rollback()


def test_source_document_status_enum_rejected(db_session):
    item = _make_item(db_session)
    with pytest.raises(IntegrityError):
        db_session.execute(
            SourceDocument.__table__.insert().values(
                service_item_id=item.id,
                title="通知",
                department="学生工作处",
                official_url="https://example.edu.cn/notice/x",
                publish_date=date(2026, 9, 1),
                effective_from=date(2026, 9, 1),
                effective_to=date(2027, 8, 31),
                audience="本科生",
                campus="主校区",
                status="bogus",
                version="v1.0",
            )
        )
    db_session.rollback()


def test_conversation_result_status_enum_rejected(db_session):
    _make_item(db_session)
    with pytest.raises(IntegrityError):
        db_session.execute(
            Conversation.__table__.insert().values(
                id="demo-conv-1", question="q", result_status="bogus"
            )
        )
    db_session.rollback()


def test_feedback_reason_code_enum_rejected(db_session):
    item = _make_item(db_session)
    conv = _make_conversation(db_session, item)
    with pytest.raises(IntegrityError):
        db_session.execute(
            Feedback.__table__.insert().values(
                conversation_id=conv.id, helpful=False, reason_code="BOGUS"
            )
        )
    db_session.rollback()


def test_feedback_reason_code_nullable_accepted(db_session):
    item = _make_item(db_session)
    conv = _make_conversation(db_session, item)
    fb = Feedback(conversation_id=conv.id, helpful=True, reason_code=None)
    db_session.add(fb)
    db_session.flush()
    assert fb.id is not None
    assert fb.created_at.tzinfo is not None
    db_session.rollback()


def test_source_document_invalid_reference_rejected(db_session):
    with pytest.raises(IntegrityError):
        db_session.add(
            SourceDocument(
                service_item_id=9999,
                title="通知",
                department="学生工作处",
                official_url="https://example.edu.cn/notice/x",
                publish_date=date(2026, 9, 1),
                effective_from=date(2026, 9, 1),
                effective_to=date(2027, 8, 31),
                audience="本科生",
                campus="主校区",
                version="v1.0",
            )
        )
        db_session.flush()
    db_session.rollback()


def test_feedback_invalid_conversation_rejected(db_session):
    with pytest.raises(IntegrityError):
        db_session.add(Feedback(conversation_id="not-exists", helpful=True))
        db_session.flush()
    db_session.rollback()


def test_source_document_effective_range_check(db_session):
    item = _make_item(db_session)
    with pytest.raises(IntegrityError):
        db_session.add(
            SourceDocument(
                service_item_id=item.id,
                title="通知",
                department="学生工作处",
                official_url="https://example.edu.cn/notice/x",
                publish_date=date(2026, 9, 1),
                effective_from=date(2027, 8, 31),
                effective_to=date(2026, 9, 1),
                audience="本科生",
                campus="主校区",
                version="v1.0",
            )
        )
        db_session.flush()
    db_session.rollback()


def test_conversation_last_intent_foreign_key(db_session):
    item = _make_item(db_session, code="S03")
    conv = _make_conversation(db_session, item)
    assert conv.last_intent == "S03"
    with pytest.raises(IntegrityError):
        db_session.add(
            Conversation(question="q", result_status=AnswerStatus.ANSWERED, last_intent="S99")
        )
        db_session.flush()
    db_session.rollback()