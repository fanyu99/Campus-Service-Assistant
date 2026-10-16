from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import KnowledgeStatus, ServiceItem, SourceDocument

EXPECTED_KEYS = {
    "id",
    "service_item_id",
    "item_code",
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
INVALID_STATUS_BODY = {
    "error": {"code": "INVALID_REQUEST", "message": "请求参数校验失败"}
}


def _item(db_session, code: str, name: str) -> ServiceItem:
    item = ServiceItem(code=code, name=name, category="测试", description="d")
    db_session.add(item)
    db_session.commit()
    return item


def _document(
    db_session,
    item,
    *,
    title: str,
    status: KnowledgeStatus,
    publish_date: date,
    official_url: str = "https://its.suda.edu.cn/2328/list.htm",
) -> SourceDocument:
    document = SourceDocument(
        service_item_id=item.id,
        title=title,
        department="学生工作处",
        official_url=official_url,
        publish_date=publish_date,
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 8, 31),
        audience="全日制在校本科生",
        campus="各校区",
        status=status,
        version="v2026.10",
        reviewed_at=date(2026, 10, 16),
        content="正文",
    )
    db_session.add(document)
    db_session.commit()
    return document


def _seed(db_session) -> None:
    s01 = _item(db_session, "S01", "学生证补办")
    s02 = _item(db_session, "S02", "校园卡补办")
    _document(
        db_session,
        s01,
        title="学生证补办流程（核验版）",
        status=KnowledgeStatus.VERIFIED,
        publish_date=date(2026, 9, 1),
    )
    _document(
        db_session,
        s01,
        title="学生证补办旧通知",
        status=KnowledgeStatus.EXPIRED,
        publish_date=date(2026, 1, 1),
    )
    _document(
        db_session,
        s02,
        title="校园卡补办草稿",
        status=KnowledgeStatus.DRAFT,
        publish_date=date(2026, 5, 1),
    )


def test_knowledge_sources_empty_returns_zero(db_client: TestClient):
    resp = db_client.get("/api/knowledge/sources")
    assert resp.status_code == 200
    assert resp.json() == {"sources": [], "total": 0}


def test_knowledge_sources_shape_and_sorting(db_client: TestClient, db_session):
    _seed(db_session)
    resp = db_client.get("/api/knowledge/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert [item["title"] for item in body["sources"]] == [
        "学生证补办流程（核验版）",
        "校园卡补办草稿",
        "学生证补办旧通知",
    ]
    for item in body["sources"]:
        assert set(item) == EXPECTED_KEYS
        assert isinstance(item["id"], str)
        assert isinstance(item["service_item_id"], str)
        assert item["item_code"] in {"S01", "S02"}
        assert item["status"] in {"draft", "verified", "expired", "conflict"}
    first = body["sources"][0]
    assert first["publish_date"] == "2026-09-01"
    assert first["effective_from"] == "2026-01-01"
    assert first["effective_to"] == "2027-08-31"
    assert first["reviewed_at"] == "2026-10-16"
    assert first["official_url"].startswith("https://")


def test_knowledge_sources_filter_by_status(db_client: TestClient, db_session):
    _seed(db_session)
    resp = db_client.get("/api/knowledge/sources?status=verified")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert [item["status"] for item in body["sources"]] == ["verified"]


def test_knowledge_sources_filter_by_item_code(db_client: TestClient, db_session):
    _seed(db_session)
    resp = db_client.get("/api/knowledge/sources?item_code=S02")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["sources"][0]["item_code"] == "S02"


def test_knowledge_sources_combined_filters(db_client: TestClient, db_session):
    _seed(db_session)
    resp = db_client.get("/api/knowledge/sources?status=expired&item_code=S01")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["sources"][0]["title"] == "学生证补办旧通知"


def test_knowledge_sources_unknown_item_code_returns_empty(db_client: TestClient, db_session):
    _seed(db_session)
    resp = db_client.get("/api/knowledge/sources?item_code=S09")
    assert resp.status_code == 200
    assert resp.json() == {"sources": [], "total": 0}


def test_knowledge_sources_invalid_status_rejected(db_client: TestClient):
    resp = db_client.get("/api/knowledge/sources?status=bogus")
    assert resp.status_code == 422
    assert resp.json() == INVALID_STATUS_BODY


def test_knowledge_sources_is_readonly(db_client: TestClient, db_session):
    _seed(db_session)
    before = db_session.scalars(select(SourceDocument)).all()
    first = db_client.get("/api/knowledge/sources")
    second = db_client.get("/api/knowledge/sources")
    assert first.json() == second.json()
    db_session.expire_all()
    after = db_session.scalars(select(SourceDocument)).all()
    assert len(after) == len(before)
