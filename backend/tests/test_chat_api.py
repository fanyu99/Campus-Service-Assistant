from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import (
    AnswerStatus,
    Conversation,
    KnowledgeStatus,
    ServiceItem,
    SourceDocument,
)
from app.services.chat_service import UNVERIFIED_WARNING
from app.services.llm_client import (
    LLMTimeoutError,
    LLMUpstreamError,
    MockLLMClient,
    get_llm_client,
)

TOKEN = "11111111-2222-3333-4444-555555555555"
OTHER_TOKEN = "99999999-8888-7777-6666-555555555555"
VALID_CARD = (
    '{"title": "学生证补办", "summary": "提交补办申请后按通知领取新证。", '
    '"eligibility": ["学生证遗失"], "materials": ["有效身份证明"], '
    '"steps": ["提交材料", "等待审核"], "location": "以最新通知为准", '
    '"deadline": null, "contacts": [], "warnings": []}'
)
BODY = "办理条件：学生证遗失。\n所需材料：有效身份证明。"


def _use_llm(db_client: TestClient, llm: MockLLMClient) -> None:
    db_client.app.dependency_overrides[get_llm_client] = lambda: llm


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
    effective_from=date(2026, 1, 1),
    effective_to=date(2027, 12, 31),
    campus="主校区",
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
        audience="全日制在校本科生",
        campus=campus,
        status=status,
        version="v1.0",
        reviewed_at=date(2026, 9, 15),
        content=content,
    )
    db_session.add(document)
    db_session.commit()
    return document


def _post(db_client: TestClient, message: str, conversation_id=None, token=TOKEN):
    headers = {"X-Session-Token": token} if token else {}
    return db_client.post(
        "/api/chat/messages",
        json={"conversation_id": conversation_id, "message": message},
        headers=headers,
    )


def test_answered_creates_conversation_and_returns_card(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))

    resp = _post(db_client, "学生证丢了怎么补办？")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "answered"
    assert body["intent"] == "S01"
    assert body["need_clarification"] is False
    assert body["clarifying_question"] is None
    assert body["answer"]["title"] == "学生证补办"
    assert body["answer"]["steps"] == ["提交材料", "等待审核"]
    assert body["sources"] == [
        {
            "title": "关于学生证补办工作的通知",
            "department": "学生工作处",
            "published_at": "2026-09-01",
            "url": "https://example.edu.cn/notice/001",
            "item_code": "S01",
            "status": "verified",
        }
    ]

    conversation = db_session.scalars(select(Conversation)).one()
    assert conversation.id == body["conversation_id"]
    assert conversation.question == "学生证丢了怎么补办？"
    assert conversation.last_intent == "S01"
    assert conversation.result_status is AnswerStatus.ANSWERED
    assert conversation.session_token == TOKEN


def test_conversation_appears_in_history_with_token(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    _post(db_client, "学生证丢了怎么补办？")

    resp = db_client.get("/api/conversations", headers={"X-Session-Token": TOKEN})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["conversations"][0]["question"] == "学生证丢了怎么补办？"
    assert body["conversations"][0]["result_status"] == "answered"

    other = db_client.get("/api/conversations", headers={"X-Session-Token": OTHER_TOKEN})
    assert other.json() == {"conversations": [], "total": 0}


def test_continuation_reuses_same_conversation(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    llm = MockLLMClient(default=VALID_CARD)
    _use_llm(db_client, llm)

    first = _post(db_client, "学生证丢了怎么补办？").json()
    second = _post(db_client, "学生证补办需要准备照片吗？", conversation_id=first["conversation_id"])

    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]
    assert db_session.scalar(select(func.count()).select_from(Conversation)) == 1
    conversation = db_session.scalars(select(Conversation)).one()
    assert conversation.question == "学生证补办需要准备照片吗？"
    # 多轮上下文（上一轮问题）被带进第二轮提示词
    assert "上一轮问题：学生证丢了怎么补办？" in llm.calls[-1][1]


def test_clarifying_answer_continues_previous_intent(db_client, db_session):
    """追问后用户只回关键参数（不含事项关键词）时，应沿用上一轮事项而非判为暂不支持。"""
    item = _item(db_session, code="S04", name="请假办理")
    _document(db_session, item, title="关于请假办理的通知")
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))

    first = _post(db_client, "我想请假。").json()
    assert first["status"] == "need_clarification"
    second = _post(db_client, "病假，三天", conversation_id=first["conversation_id"]).json()

    assert second["conversation_id"] == first["conversation_id"]
    assert second["intent"] == "S04"
    assert second["status"] == "answered"
    assert second["answer"]["title"] == "学生证补办"  # 替身返回的固定卡片


def test_still_clarifies_when_parameter_still_missing(db_client, db_session):
    _item(db_session, code="S04", name="请假办理")
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "我想请假。").json()
    second = _post(db_client, "就是想请假", conversation_id=first["conversation_id"]).json()
    assert second["status"] == "need_clarification"
    assert second["intent"] == "S04"


def test_unsupported_follow_up_after_answer_is_not_inherited(db_client, db_session):
    """上一轮不是追问时，不承接事项：无关问题仍按暂不支持处理。"""
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？").json()
    second = _post(db_client, "食堂几点开门？", conversation_id=first["conversation_id"]).json()
    assert second["status"] == "unsupported"


def test_unknown_conversation_id_returns_404(db_client, db_session):
    _use_llm(db_client, MockLLMClient())
    resp = _post(db_client, "学生证丢了怎么补办？", conversation_id="not-exists")
    assert resp.status_code == 404
    assert resp.json() == {
        "error": {"code": "CONVERSATION_NOT_FOUND", "message": "会话不存在或已过期"}
    }


def test_message_too_long_rejected_without_creating_conversation(db_client, db_session):
    _use_llm(db_client, MockLLMClient())
    resp = _post(db_client, "字" * 201)
    assert resp.status_code == 400
    assert resp.json() == {
        "error": {"code": "MESSAGE_TOO_LONG", "message": "message 不能超过 200 个字符"}
    }
    assert db_session.scalar(select(func.count()).select_from(Conversation)) == 0


def test_blank_message_rejected(db_client):
    resp = _post(db_client, "   ")
    assert resp.status_code == 422


def test_need_clarification_for_incomplete_leave_request(db_client, db_session):
    _item(db_session, code="S04", name="请假办理")
    _use_llm(db_client, MockLLMClient())
    body = _post(db_client, "我想请假。").json()
    assert body["status"] == "need_clarification"
    assert body["intent"] == "S04"
    assert body["need_clarification"] is True
    assert body["clarifying_question"] == "你的请假类型是事假、病假还是公假？"
    assert body["answer"] is None
    assert body["sources"] == []


def test_cross_item_question_asks_which_one(db_client, db_session):
    _item(db_session, code="S01", name="学生证补办")
    _item(db_session, code="S02", name="校园卡补办")
    _use_llm(db_client, MockLLMClient())
    body = _post(db_client, "学生证和校园卡都丢了怎么办？").json()
    assert body["status"] == "need_clarification"
    assert body["intent"] is None
    assert "学生证补办" in body["clarifying_question"]
    assert "校园卡补办" in body["clarifying_question"]


def test_unsupported_question_returns_supported_hint(db_client, db_session):
    _use_llm(db_client, MockLLMClient())
    body = _post(db_client, "食堂几点开门？").json()
    assert body["status"] == "unsupported"
    assert body["intent"] is None
    assert body["answer"] is None
    assert body["sources"] == []
    assert body["need_clarification"] is False


def test_matched_item_without_documents_is_insufficient(db_client, db_session):
    _item(db_session, code="S02", name="校园卡补办")
    _use_llm(db_client, MockLLMClient())
    body = _post(db_client, "校园卡丢了怎么补办？").json()
    assert body["status"] == "insufficient_evidence"
    assert body["intent"] == "S02"
    assert body["answer"] is None
    assert body["sources"] == []


def test_expired_only_evidence_is_refused(db_client, db_session):
    item = _item(db_session)
    _document(
        db_session,
        item,
        status=KnowledgeStatus.EXPIRED,
        effective_from=date(2025, 1, 1),
        effective_to=date(2025, 12, 31),
    )
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    body = _post(db_client, "学生证丢了怎么补办？").json()
    assert body["status"] == "insufficient_evidence"
    assert body["answer"] is None
    # 回带过期来源，前端可提示「资料可能已失效」（实施方案用例 4）
    assert [source["status"] for source in body["sources"]] == ["expired"]


def test_conflict_documents_return_conflict_state(db_client, db_session):
    item = _item(db_session, code="S07", name="转专业咨询")
    _document(
        db_session,
        item,
        status=KnowledgeStatus.CONFLICT,
        title="院级转专业通知",
    )
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    body = _post(db_client, "转专业需要什么条件？").json()
    assert body["status"] == "conflict"
    assert body["intent"] == "S07"
    assert body["answer"] is None
    assert [source["status"] for source in body["sources"]] == ["conflict"]


def test_model_reports_insufficient_evidence(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(
        db_client,
        MockLLMClient(default='{"status": "insufficient_evidence"}'),
    )
    body = _post(db_client, "学生证丢了怎么补办？").json()
    assert body["status"] == "insufficient_evidence"
    assert body["answer"] is None


def test_invalid_model_output_degrades_to_service_error(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default="抱歉，我不确定该怎么回答。"))
    body = _post(db_client, "学生证丢了怎么补办？").json()
    assert body["status"] == "service_error"
    assert body["answer"] is None
    assert body["sources"] == []
    conversation = db_session.scalars(select(Conversation)).one()
    assert conversation.result_status is AnswerStatus.SERVICE_ERROR


def test_answer_null_is_explicit_and_sources_always_list(db_client, db_session):
    _item(db_session, code="S04", name="请假办理")
    _use_llm(db_client, MockLLMClient())
    for message, expected in (
        ("我想请假。", "need_clarification"),
        ("食堂几点开门？", "unsupported"),
    ):
        body = _post(db_client, message).json()
        assert body["status"] == expected
        assert "answer" in body
        assert body["answer"] is None
        assert isinstance(body["sources"], list)


def test_warning_added_when_unverified_documents_exist(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _document(db_session, item, status=KnowledgeStatus.DRAFT, title="草稿通知")
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    body = _post(db_client, "学生证丢了怎么补办？").json()
    assert body["status"] == "answered"
    assert UNVERIFIED_WARNING in body["answer"]["warnings"]


def test_llm_upstream_failure_returns_503_and_persists_nothing(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(error=LLMUpstreamError("挂了", status_code=500)))
    resp = _post(db_client, "学生证丢了怎么补办？")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_ERROR"
    assert db_session.scalar(select(func.count()).select_from(Conversation)) == 0


def test_llm_rate_limit_maps_to_429(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(error=LLMUpstreamError("限流", status_code=429)))
    resp = _post(db_client, "学生证丢了怎么补办？")
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "RATE_LIMITED"


def test_llm_timeout_maps_to_503(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(error=LLMTimeoutError("慢")))
    resp = _post(db_client, "学生证丢了怎么补办？")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_TIMEOUT"


def test_chat_without_token_still_works(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    body = _post(db_client, "学生证丢了怎么补办？", token=None).json()
    assert body["status"] == "answered"
    conversation = db_session.scalars(select(Conversation)).one()
    assert conversation.session_token is None


def test_token_is_adopted_by_existing_conversation(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？", token=None).json()
    _post(db_client, "需要照片吗？", conversation_id=first["conversation_id"], token=TOKEN)
    db_session.expire_all()
    conversation = db_session.scalars(select(Conversation)).one()
    assert conversation.session_token == TOKEN


def test_continuation_with_other_token_is_rejected(db_client, db_session):
    """禁止跨标识续写（契约 §4.4 匿名隔离）。"""
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？", token=TOKEN).json()
    resp = _post(
        db_client, "还需要照片吗？", conversation_id=first["conversation_id"], token=OTHER_TOKEN
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_continuation_without_token_is_rejected_for_owned_conversation(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))
    first = _post(db_client, "学生证丢了怎么补办？", token=TOKEN).json()
    resp = _post(db_client, "还需要照片吗？", conversation_id=first["conversation_id"], token=None)
    assert resp.status_code == 404


def test_context_is_included_in_prompt(db_client, db_session):
    item = _item(db_session)
    _document(db_session, item)
    llm = MockLLMClient(default=VALID_CARD)
    _use_llm(db_client, llm)
    db_client.post(
        "/api/chat/messages",
        json={
            "conversation_id": None,
            "message": "学生证丢了怎么补办？",
            "context": {"campus": "主校区", "student_type": "undergraduate"},
        },
        headers={"X-Session-Token": TOKEN},
    )
    prompt = llm.calls[-1][1]
    assert "【校区】主校区" in prompt
    assert "【学生类型】undergraduate" in prompt
    assert "办理条件：学生证遗失。" in prompt


@pytest.mark.parametrize("message", ["", "   "])
def test_empty_message_rejected(db_client, message):
    resp = db_client.post(
        "/api/chat/messages", json={"conversation_id": None, "message": message}
    )
    assert resp.status_code == 422
