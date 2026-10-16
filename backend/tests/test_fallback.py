from datetime import date

from fastapi.testclient import TestClient

from app.models import KnowledgeStatus, ServiceItem, SourceDocument
from app.services.fallback_service import (
    RATE_LIMITED_MESSAGE,
    UPSTREAM_ERROR_MESSAGE,
    UPSTREAM_TIMEOUT_MESSAGE,
    service_error_response,
    to_business_error,
)
from app.services.llm_client import (
    LLMError,
    LLMTimeoutError,
    LLMUpstreamError,
    MockLLMClient,
    get_llm_client,
)


def test_timeout_maps_to_upstream_timeout():
    error = to_business_error(LLMTimeoutError("慢"))
    assert error.status_code == 503
    assert error.code == "UPSTREAM_TIMEOUT"
    assert error.message == UPSTREAM_TIMEOUT_MESSAGE


def test_upstream_rate_limit_maps_to_rate_limited():
    error = to_business_error(LLMUpstreamError("限流", status_code=429))
    assert error.status_code == 429
    assert error.code == "RATE_LIMITED"
    assert error.message == RATE_LIMITED_MESSAGE


def test_upstream_failure_maps_to_upstream_error():
    error = to_business_error(LLMUpstreamError("挂了", status_code=500))
    assert error.status_code == 503
    assert error.code == "UPSTREAM_ERROR"
    assert error.message == UPSTREAM_ERROR_MESSAGE


def test_unknown_llm_error_maps_to_upstream_error():
    error = to_business_error(LLMError("未知"))
    assert error.status_code == 503
    assert error.code == "UPSTREAM_ERROR"


def test_service_error_response_shape():
    body = service_error_response("conv-1", intent="S01")
    assert body.status.value == "service_error"
    assert body.answer is None
    assert body.sources == []
    assert body.need_clarification is False
    assert body.clarifying_question is None


def _seed_grounded_item(db_session) -> ServiceItem:
    item = ServiceItem(code="S01", name="学生证补办", category="证件", description="d")
    db_session.add(item)
    db_session.commit()
    db_session.add(
        SourceDocument(
            service_item_id=item.id,
            title="关于学生证补办工作的通知",
            department="学生工作处",
            official_url="https://example.edu.cn/notice/001",
            publish_date=date(2026, 9, 1),
            effective_from=date(2026, 1, 1),
            effective_to=date(2027, 12, 31),
            audience="全日制在校本科生",
            campus="主校区",
            status=KnowledgeStatus.VERIFIED,
            version="v1.0",
            content="办理条件：学生证遗失。",
        )
    )
    db_session.commit()
    return item


def test_endpoint_returns_503_when_llm_times_out(db_client: TestClient, db_session):
    _seed_grounded_item(db_session)
    db_client.app.dependency_overrides[get_llm_client] = lambda: MockLLMClient(
        error=LLMTimeoutError("慢")
    )
    resp = db_client.post(
        "/api/chat/messages", json={"conversation_id": None, "message": "学生证丢了怎么补办？"}
    )
    assert resp.status_code == 503
    assert resp.json() == {
        "error": {"code": "UPSTREAM_TIMEOUT", "message": UPSTREAM_TIMEOUT_MESSAGE}
    }
