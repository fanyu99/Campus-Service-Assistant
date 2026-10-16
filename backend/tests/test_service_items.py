from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import ServiceItem
from app.services.service_items import ALLOWED_TONES, CONTRACT_ID_MAP, DISPLAY_DEFAULTS

EXPECTED_ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"]


def _seed_items(db_session, specs: list[dict]) -> None:
    for spec in specs:
        db_session.add(ServiceItem(**spec))
    db_session.commit()


def test_service_items_all_contract_items(db_client: TestClient, db_session):
    _seed_items(db_session, [
        {"code": code, "name": name, "category": "证件", "description": "说明"}
        for code, name in [
            ("S01", "学生证补办"),
            ("S02", "校园卡补办"),
            ("S03", "宿舍报修"),
            ("S04", "请假办理"),
            ("S05", "奖学金申请"),
            ("S06", "助学金申请"),
            ("S07", "转专业咨询"),
            ("S08", "毕业手续"),
        ]
    ])
    resp = db_client.get("/api/service-items")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 8
    for item in items:
        assert set(item) == {
            "id",
            "title",
            "description",
            "category",
            "icon",
            "tone",
            "prompt",
        }
        # 契约 §3.1 的选返字段：8 项事项必须齐全（缺省表兜底）
        assert item["icon"]
        assert item["tone"] in {"orange", "blue", "green", "purple"}
        assert item["prompt"]
    titles = {item["id"]: item["title"] for item in items}
    assert titles["student-card"] == "学生证补办"
    assert titles["campus-card"] == "校园卡补办"
    assert titles["repair"] == "宿舍报修"
    assert titles["leave"] == "请假办理"
    assert titles["scholarship"] == "奖学金申请"
    assert titles["grant"] == "助学金申请"
    assert titles["major-transfer"] == "转专业咨询"
    assert titles["graduation"] == "毕业手续"


def test_service_items_sorted_by_code(db_client: TestClient, db_session):
    _seed_items(db_session, [
        {"code": "S03", "name": "宿舍报修", "category": "生活", "description": "d"},
        {"code": "S01", "name": "学生证补办", "category": "证件", "description": "d"},
        {"code": "S02", "name": "校园卡补办", "category": "证件", "description": "d"},
    ])
    resp = db_client.get("/api/service-items")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert ids == ["student-card", "campus-card", "repair"]


def test_service_items_excludes_disabled(db_client: TestClient, db_session):
    _seed_items(db_session, [
        {"code": "S01", "name": "学生证补办", "category": "证件", "description": "d"},
        {"code": "S02", "name": "校园卡补办", "category": "证件", "description": "d", "enabled": False},
    ])
    resp = db_client.get("/api/service-items")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert ids == ["student-card"]
    remaining = db_session.scalars(select(ServiceItem.code)).all()
    assert sorted(remaining) == ["S01", "S02"]


def test_service_items_empty_table_returns_empty_array(db_client: TestClient):
    resp = db_client.get("/api/service-items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_service_items_unknown_code_lowercase_fallback(db_client: TestClient, db_session):
    _seed_items(db_session, [
        {"code": "S09", "name": "新事项", "category": "其他", "description": "d"},
    ])
    resp = db_client.get("/api/service-items")
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "s09"


def test_service_items_idempotent(db_client: TestClient, db_session):
    _seed_items(db_session, [
        {"code": "S01", "name": "学生证补办", "category": "证件", "description": "d"},
    ])
    first = db_client.get("/api/service-items")
    second = db_client.get("/api/service-items")
    assert first.json() == second.json()


def test_service_items_post_method_not_allowed(db_client: TestClient):
    resp = db_client.post("/api/service-items")
    assert resp.status_code == 405
    assert resp.json() == {
        "error": {"code": "INVALID_REQUEST", "message": "请求方法不支持"}
    }


def test_contract_id_map_matches_docs():
    assert CONTRACT_ID_MAP == {
        "S01": "student-card",
        "S02": "campus-card",
        "S03": "repair",
        "S04": "leave",
        "S05": "scholarship",
        "S06": "grant",
        "S07": "major-transfer",
        "S08": "graduation",
    }


def test_service_items_display_defaults_cover_all_contract_codes():
    assert set(DISPLAY_DEFAULTS) == set(CONTRACT_ID_MAP)
    for defaults in DISPLAY_DEFAULTS.values():
        assert set(defaults) == {"icon", "tone", "prompt"}


def test_display_defaults_use_contract_tone_values():
    """契约 §3.1 限定 tone 取值，缺省表必须落在枚举内。"""
    for code, defaults in DISPLAY_DEFAULTS.items():
        assert defaults["tone"] in ALLOWED_TONES, code


def test_display_defaults_icons_match_frontend_rendering():
    """与前端 `src/data/service-icons.ts` 的有效渲染结果一致（未映射项回退 i-doc），
    避免后端一个图标、前端渲染另一个的双来源漂移。"""
    expected = {
        "S01": "i-id",
        "S02": "i-card",
        "S03": "i-wrench",
        "S04": "i-calendar",
        "S05": "i-award",
        "S06": "i-doc",
        "S07": "i-doc",
        "S08": "i-doc",
    }
    assert {code: values["icon"] for code, values in DISPLAY_DEFAULTS.items()} == expected


def test_service_items_database_display_values_win_over_defaults(
    db_client: TestClient, db_session
):
    _seed_items(db_session, [
        {
            "code": "S01",
            "name": "学生证补办",
            "category": "证件",
            "description": "d",
            "icon": "i-custom",
            "tone": "green",
            "prompt": "自定义问题？",
        },
    ])
    resp = db_client.get("/api/service-items")
    item = resp.json()[0]
    assert item["icon"] == "i-custom"
    assert item["tone"] == "green"
    assert item["prompt"] == "自定义问题？"


def test_service_items_unknown_code_has_null_display_fields(
    db_client: TestClient, db_session
):
    _seed_items(db_session, [
        {"code": "S09", "name": "新事项", "category": "其他", "description": "d"},
    ])
    item = db_client.get("/api/service-items").json()[0]
    assert item["id"] == "s09"
    assert item["icon"] is None
    assert item["tone"] is None
    assert item["prompt"] is None