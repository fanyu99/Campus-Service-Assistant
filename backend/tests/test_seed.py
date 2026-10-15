from sqlalchemy import func, select

from app.models import (
    Conversation,
    Feedback,
    FeedbackReasonCode,
    KnowledgeStatus,
    ServiceItem,
    SourceDocument,
)
from scripts.seed_demo_data import seed_demo_data

EXPECTED_COUNTS = {
    "service_items": 8,
    "source_documents": 8,
    "conversations": 5,
    "feedback": 5,
}


def _counts(session) -> dict:
    return {
        "service_items": session.scalar(select(func.count()).select_from(ServiceItem)),
        "source_documents": session.scalar(
            select(func.count()).select_from(SourceDocument)
        ),
        "conversations": session.scalar(
            select(func.count()).select_from(Conversation)
        ),
        "feedback": session.scalar(select(func.count()).select_from(Feedback)),
    }


def test_seed_idempotent(db_session):
    seed_demo_data(db_session)
    after_first = _counts(db_session)
    seed_demo_data(db_session)
    after_second = _counts(db_session)
    assert after_first == EXPECTED_COUNTS
    assert after_second == EXPECTED_COUNTS


def test_seed_covers_contract_mapping(db_session):
    seed_demo_data(db_session)
    items = {
        item.code: item.name
        for item in db_session.execute(select(ServiceItem)).scalars()
    }
    assert set(items) == {"S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"}
    assert items["S01"] == "学生证补办"
    assert items["S02"] == "校园卡补办"
    assert items["S03"] == "宿舍报修"
    assert items["S04"] == "请假办理"
    assert items["S05"] == "奖学金申请"
    assert items["S06"] == "助学金申请"
    assert items["S07"] == "转专业咨询"
    assert items["S08"] == "毕业手续"


def test_seed_urls_are_absolute_http(db_session):
    seed_demo_data(db_session)
    urls = db_session.execute(select(SourceDocument.official_url)).scalars().all()
    assert urls
    for url in urls:
        assert url.startswith("http://") or url.startswith("https://")


def test_seed_covers_knowledge_status(db_session):
    seed_demo_data(db_session)
    statuses = db_session.execute(select(SourceDocument.status)).scalars().all()
    assert set(statuses) == set(KnowledgeStatus)


def test_seed_conversations_no_pii(db_session):
    seed_demo_data(db_session)
    cols = {c.name for c in Conversation.__table__.columns}
    banned = {"name", "real_name", "student_id", "id_card", "bank_card", "password", "phone"}
    assert not cols & banned
    questions = db_session.execute(select(Conversation.question)).scalars().all()
    for question in questions:
        for keyword in ("学号", "身份证", "银行卡", "密码"):
            assert keyword not in question


def test_seed_feedback_reason_codes(db_session):
    seed_demo_data(db_session)
    reason_codes = (
        db_session.execute(select(Feedback.reason_code)).scalars().all()
    )
    assert set(reason_codes) == {
        None,
        FeedbackReasonCode.SOURCE_ERROR,
        FeedbackReasonCode.INCOMPLETE_STEPS,
        FeedbackReasonCode.OUTDATED_CONTENT,
        FeedbackReasonCode.OTHER,
    }