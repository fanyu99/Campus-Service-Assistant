from datetime import date

from app.models import AnswerStatus, KnowledgeStatus, ServiceItem, SourceDocument
from app.schemas.chat import ChatContext
from app.services.retrieval import MAX_SNIPPETS, retrieve_documents

IN_EFFECT_FROM = date(2026, 1, 1)
IN_EFFECT_TO = date(2027, 12, 31)
EXPIRED_FROM = date(2025, 1, 1)
EXPIRED_TO = date(2025, 12, 31)
BODY = "办理条件：学生证遗失。\n所需材料：身份证明。"


def _item(db_session, code="S01", name="学生证补办") -> ServiceItem:
    item = ServiceItem(code=code, name=name, category="证件", description="d")
    db_session.add(item)
    db_session.commit()
    return item


def _document(
    db_session,
    item,
    *,
    status=KnowledgeStatus.VERIFIED,
    content=BODY,
    effective_from=IN_EFFECT_FROM,
    effective_to=IN_EFFECT_TO,
    campus="主校区",
    audience="全日制在校本科生",
    title="关于学生证补办工作的通知",
) -> SourceDocument:
    document = SourceDocument(
        service_item_id=item.id,
        title=title,
        department="学生工作处",
        official_url="https://example.edu.cn/notice/001",
        publish_date=date(2026, 9, 1),
        effective_from=effective_from,
        effective_to=effective_to,
        audience=audience,
        campus=campus,
        status=status,
        version="v1.0",
        reviewed_at=date(2026, 9, 15),
        content=content,
    )
    db_session.add(document)
    db_session.commit()
    return document


def test_verified_in_effect_document_is_grounded(db_session):
    item = _item(db_session)
    _document(db_session, item)
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.ANSWERED
    assert len(outcome.documents) == 1
    assert outcome.sources[0].url == "https://example.edu.cn/notice/001"
    assert outcome.sources[0].item_code == "S01"
    assert outcome.sources[0].status == "verified"
    assert outcome.sources[0].published_at == "2026-09-01"
    assert outcome.has_unverified is False


def test_unknown_intent_code_is_insufficient(db_session):
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert outcome.sources == ()


def test_item_without_documents_is_insufficient(db_session):
    _item(db_session, code="S02")
    outcome = retrieve_documents(db_session, "S02")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert outcome.sources == ()


def test_expired_only_is_insufficient(db_session):
    """过期资料不得作为唯一依据（实施方案 7.5 / 用例 4），但要回带来源供前端提示。"""
    item = _item(db_session)
    _document(
        db_session,
        item,
        status=KnowledgeStatus.EXPIRED,
        effective_from=EXPIRED_FROM,
        effective_to=EXPIRED_TO,
    )
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert outcome.documents == ()
    assert [source.status for source in outcome.sources] == ["expired"]
    assert outcome.has_unverified is True


def test_draft_only_is_insufficient(db_session):
    item = _item(db_session)
    _document(db_session, item, status=KnowledgeStatus.DRAFT)
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert [source.status for source in outcome.sources] == ["draft"]


def test_no_documents_returns_no_sources(db_session):
    _item(db_session, code="S02")
    outcome = retrieve_documents(db_session, "S02")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert outcome.sources == ()


def test_student_type_english_value_matches_chinese_audience(db_session):
    """契约示例用 undergraduate，而 audience 是中文描述，需要口径映射。"""
    item = _item(db_session)
    _document(db_session, item, audience="全日制在校本科生")
    _document(db_session, item, audience="在校研究生", title="研究生通知")
    outcome = retrieve_documents(db_session, "S01", ChatContext(student_type="graduate"))
    assert len(outcome.documents) == 1
    assert "研究生" in outcome.documents[0].audience


def test_student_type_filter_is_soft_when_no_match(db_session):
    item = _item(db_session)
    _document(db_session, item, audience="全日制在校本科生")
    outcome = retrieve_documents(db_session, "S01", ChatContext(student_type="visiting"))
    assert outcome.status is AnswerStatus.ANSWERED
    assert len(outcome.documents) == 1


def test_verified_without_content_is_insufficient(db_session):
    """已核验但正文为空：没有可依据的片段，仍按拒答处理。"""
    item = _item(db_session)
    _document(db_session, item, content="   ")
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.INSUFFICIENT_EVIDENCE


def test_conflict_document_takes_priority(db_session):
    item = _item(db_session)
    _document(db_session, item)
    _document(db_session, item, status=KnowledgeStatus.CONFLICT, title="院级通知")
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.CONFLICT
    assert [source.status for source in outcome.sources] == ["conflict"]


def test_campus_filter_narrows_when_matched(db_session):
    item = _item(db_session)
    _document(db_session, item, campus="主校区")
    _document(db_session, item, campus="分校区", title="分校区通知")
    outcome = retrieve_documents(db_session, "S01", ChatContext(campus="分校区"))
    assert len(outcome.documents) == 1
    assert outcome.documents[0].campus == "分校区"


def test_campus_filter_is_soft_when_no_match(db_session):
    """数据缺失时不做硬过滤，避免误拒答。"""
    item = _item(db_session)
    _document(db_session, item, campus="主校区")
    outcome = retrieve_documents(db_session, "S01", ChatContext(campus="不存在的校区"))
    assert outcome.status is AnswerStatus.ANSWERED
    assert len(outcome.documents) == 1


def test_snippets_are_capped(db_session):
    item = _item(db_session)
    for index in range(MAX_SNIPPETS + 3):
        _document(db_session, item, title=f"通知 {index}")
    outcome = retrieve_documents(db_session, "S01")
    assert len(outcome.documents) == MAX_SNIPPETS


def test_unverified_flag_set_when_other_documents_exist(db_session):
    item = _item(db_session)
    _document(db_session, item)
    _document(db_session, item, status=KnowledgeStatus.DRAFT, title="草稿通知")
    outcome = retrieve_documents(db_session, "S01")
    assert outcome.status is AnswerStatus.ANSWERED
    assert outcome.has_unverified is True
