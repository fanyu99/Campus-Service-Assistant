import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import create_db_engine, create_session_factory
from app.models import (
    AnswerStatus,
    Conversation,
    Feedback,
    FeedbackReasonCode,
    KnowledgeStatus,
    ServiceItem,
    SourceDocument,
)

REQUIRED_TABLES = {"service_items", "source_documents", "conversations", "feedback"}

SERVICE_ITEMS = [
    {"code": "S01", "name": "学生证补办", "category": "证件", "description": "材料、流程与办理地点"},
    {"code": "S02", "name": "校园卡补办", "category": "证件", "description": "挂失、补办与领取流程"},
    {"code": "S03", "name": "宿舍报修", "category": "生活", "description": "报修渠道与处理时限"},
    {"code": "S04", "name": "请假办理", "category": "生活", "description": "请假类型与审批流程"},
    {"code": "S05", "name": "奖学金申请", "category": "学业", "description": "申请条件与评选流程"},
    {"code": "S06", "name": "助学金申请", "category": "学业", "description": "申请条件与材料清单"},
    {"code": "S07", "name": "转专业咨询", "category": "学业", "description": "申请窗口与考核要求"},
    {"code": "S08", "name": "毕业手续", "category": "学业", "description": "离校手续与材料办理"},
]

SOURCE_DOCUMENTS = [
    {
        "item_code": "S01",
        "title": "关于学生证补办工作的通知",
        "department": "学生工作处",
        "official_url": "https://example.edu.cn/notice/s01",
        "publish_date": date(2026, 9, 1),
        "effective_from": date(2026, 9, 1),
        "effective_to": date(2027, 8, 31),
        "audience": "全日制在校本科生",
        "campus": "主校区",
        "status": KnowledgeStatus.VERIFIED,
        "version": "v1.0",
        "reviewed_at": date(2026, 9, 15),
    },
    {
        "item_code": "S02",
        "title": "关于校园卡补办流程的通知",
        "department": "信息化办公室",
        "official_url": "https://example.edu.cn/notice/s02",
        "publish_date": date(2026, 9, 3),
        "effective_from": date(2026, 9, 3),
        "effective_to": date(2027, 8, 31),
        "audience": "全体在校生",
        "campus": "主校区",
        "status": KnowledgeStatus.VERIFIED,
        "version": "v1.0",
        "reviewed_at": date(2026, 9, 20),
    },
    {
        "item_code": "S03",
        "title": "宿舍报修服务指南",
        "department": "后勤保障处",
        "official_url": "https://example.edu.cn/notice/s03",
        "publish_date": date(2026, 9, 5),
        "effective_from": date(2026, 9, 5),
        "effective_to": date(2027, 6, 30),
        "audience": "全体住宿生",
        "campus": "主校区",
        "status": KnowledgeStatus.DRAFT,
        "version": "v0.1",
        "reviewed_at": None,
    },
    {
        "item_code": "S04",
        "title": "关于学生请假管理办法的通知",
        "department": "教务处",
        "official_url": "https://example.edu.cn/notice/s04",
        "publish_date": date(2026, 9, 2),
        "effective_from": date(2026, 9, 2),
        "effective_to": date(2027, 8, 31),
        "audience": "全日制在校本科生",
        "campus": "主校区",
        "status": KnowledgeStatus.VERIFIED,
        "version": "v1.2",
        "reviewed_at": date(2026, 9, 25),
    },
    {
        "item_code": "S05",
        "title": "关于评选2025-2026学年奖学金的通知",
        "department": "学生工作处",
        "official_url": "https://example.edu.cn/notice/s05",
        "publish_date": date(2025, 8, 20),
        "effective_from": date(2025, 8, 20),
        "effective_to": date(2026, 6, 30),
        "audience": "全日制在校本科生",
        "campus": "主校区",
        "status": KnowledgeStatus.EXPIRED,
        "version": "v1.0",
        "reviewed_at": date(2026, 6, 30),
    },
    {
        "item_code": "S06",
        "title": "关于做好2025-2026学年助学金评定工作的通知",
        "department": "学生资助管理中心",
        "official_url": "https://example.edu.cn/notice/s06",
        "publish_date": date(2026, 8, 25),
        "effective_from": date(2026, 8, 25),
        "effective_to": date(2027, 6, 30),
        "audience": "家庭经济困难学生",
        "campus": "主校区",
        "status": KnowledgeStatus.VERIFIED,
        "version": "v1.0",
        "reviewed_at": date(2026, 9, 10),
    },
    {
        "item_code": "S07",
        "title": "关于转专业工作的通知",
        "department": "教务处",
        "official_url": "https://example.edu.cn/notice/s07",
        "publish_date": date(2026, 9, 8),
        "effective_from": date(2026, 9, 8),
        "effective_to": date(2027, 3, 31),
        "audience": "全日制在校本科生",
        "campus": "主校区",
        "status": KnowledgeStatus.CONFLICT,
        "version": "v1.1",
        "reviewed_at": None,
    },
    {
        "item_code": "S08",
        "title": "关于2026届毕业生办理离校手续的通知",
        "department": "教务处",
        "official_url": "https://example.edu.cn/notice/s08",
        "publish_date": date(2026, 6, 1),
        "effective_from": date(2026, 6, 1),
        "effective_to": date(2026, 7, 15),
        "audience": "2026届毕业生",
        "campus": "主校区",
        "status": KnowledgeStatus.DRAFT,
        "version": "v1.0",
        "reviewed_at": None,
    },
]

DEMO_SESSION_TOKEN = "5c1f7a9e-2b3d-4e5f-8a60-9b0c1d2e3f40"

DEMO_CONVERSATIONS = [
    {
        "id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e01",
        "question": "学生证丢了怎么补办？",
        "last_intent": "S01",
        "result_status": AnswerStatus.ANSWERED,
        "session_token": DEMO_SESSION_TOKEN,
    },
    {
        "id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e02",
        "question": "校园卡坏了去哪里换？",
        "last_intent": "S02",
        "result_status": AnswerStatus.ANSWERED,
        "session_token": DEMO_SESSION_TOKEN,
    },
    {
        "id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e03",
        "question": "我想请假",
        "last_intent": "S04",
        "result_status": AnswerStatus.NEED_CLARIFICATION,
        "session_token": DEMO_SESSION_TOKEN,
    },
    {
        "id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e04",
        "question": "食堂几点开门？",
        "last_intent": None,
        "result_status": AnswerStatus.UNSUPPORTED,
        "session_token": DEMO_SESSION_TOKEN,
    },
    {
        "id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e05",
        "question": "学生证补办需要照片吗？",
        "last_intent": "S01",
        "result_status": AnswerStatus.ANSWERED,
        "session_token": DEMO_SESSION_TOKEN,
    },
]

DEMO_FEEDBACK = [
    {
        "conversation_id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e01",
        "helpful": True,
        "reason_code": None,
        "comment": None,
    },
    {
        "conversation_id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e02",
        "helpful": False,
        "reason_code": FeedbackReasonCode.SOURCE_ERROR,
        "comment": None,
    },
    {
        "conversation_id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e03",
        "helpful": False,
        "reason_code": FeedbackReasonCode.INCOMPLETE_STEPS,
        "comment": None,
    },
    {
        "conversation_id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e04",
        "helpful": False,
        "reason_code": FeedbackReasonCode.OTHER,
        "comment": None,
    },
    {
        "conversation_id": "9f0d1b2e-3c4a-4d5e-8f60-1a2b3c4d5e05",
        "helpful": False,
        "reason_code": FeedbackReasonCode.OUTDATED_CONTENT,
        "comment": "办理地点似乎已经发生变化",
    },
]


@dataclass
class SeedReport:
    service_items: int = 0
    source_documents: int = 0
    conversations: int = 0
    feedback: int = 0


def seed_demo_data(session: Session) -> SeedReport:
    inspector = sa_inspect(session.get_bind())
    if not REQUIRED_TABLES <= set(inspector.get_table_names()):
        raise RuntimeError("数据库表结构未就绪，请先执行建库与 alembic upgrade head")
    report = SeedReport()
    try:
        _upsert_service_items(session, report)
        _upsert_source_documents(session, report)
        _upsert_conversations(session, report)
        _upsert_feedback(session, report)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return report


def _upsert_service_items(session: Session, report: SeedReport) -> None:
    for spec in SERVICE_ITEMS:
        obj = session.scalar(select(ServiceItem).where(ServiceItem.code == spec["code"]))
        if obj is None:
            session.add(ServiceItem(**spec))
            report.service_items += 1
        else:
            for key, value in spec.items():
                setattr(obj, key, value)


def _upsert_source_documents(session: Session, report: SeedReport) -> None:
    for spec in SOURCE_DOCUMENTS:
        item = session.scalar(
            select(ServiceItem).where(ServiceItem.code == spec["item_code"])
        )
        if item is None:
            raise RuntimeError(f"演示来源文档关联的事项 {spec['item_code']} 不存在")
        payload = {k: v for k, v in spec.items() if k != "item_code"}
        payload["service_item_id"] = item.id
        existing = session.scalar(
            select(SourceDocument).where(
                SourceDocument.service_item_id == payload["service_item_id"],
                SourceDocument.official_url == payload["official_url"],
            )
        )
        if existing is None:
            session.add(SourceDocument(**payload))
            report.source_documents += 1
        else:
            for key, value in payload.items():
                setattr(existing, key, value)


def _upsert_conversations(session: Session, report: SeedReport) -> None:
    for spec in DEMO_CONVERSATIONS:
        obj = session.get(Conversation, spec["id"])
        if obj is None:
            session.add(Conversation(**spec))
            report.conversations += 1
        else:
            for key, value in spec.items():
                setattr(obj, key, value)


def _upsert_feedback(session: Session, report: SeedReport) -> None:
    for spec in DEMO_FEEDBACK:
        existing = session.scalar(
            select(Feedback).where(Feedback.conversation_id == spec["conversation_id"])
        )
        if existing is None:
            session.add(Feedback(**spec))
            report.feedback += 1
        else:
            for key, value in spec.items():
                setattr(existing, key, value)


def main() -> None:
    engine = create_db_engine()
    try:
        with create_session_factory(engine)() as session:
            try:
                report = seed_demo_data(session)
            except RuntimeError as exc:
                print(exc)
                raise SystemExit(1) from None
            except Exception as exc:
                print(f"演示数据写入失败：{exc.__class__.__name__}，事务已回滚")
                raise SystemExit(1) from None
        print(
            f"演示数据写入完成：service_items {report.service_items} 条，"
            f"source_documents {report.source_documents} 条，"
            f"conversations {report.conversations} 条，"
            f"feedback {report.feedback} 条"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()