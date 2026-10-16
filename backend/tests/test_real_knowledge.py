"""真实知识库（scripts/real_knowledge.py）与导入器（scripts/load_real_knowledge.py）的守卫测试。

这些测试把「来源可追溯、不编造」从口头约定变成可回归的断言：
- 数据质量：8 项全覆盖、来源为 suda.edu.cn 官方地址、状态一律 verified、有效期未过、正文非空；
- 已废止口径不得回流：S01 的「教务处综合科办理」与 S07 的「3月中下旬申请」都已被调研清单
  判定为旧版（docs/suda-affairs-research-2026-10.md），一旦被写回正文即测试失败；
- 导入器：替换演示占位文档、幂等、清理旧版条目；
- 端到端：8 项事项在真实知识下都能产出 answered 并挂上真实来源。
"""

from datetime import date
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import AnswerStatus, KnowledgeStatus, ServiceItem, SourceDocument
from app.services.llm_client import MockLLMClient, get_llm_client
from scripts.load_real_knowledge import (
    DEMO_URL_MARK,
    REVIEW_TITLE_SUFFIX,
    load_real_knowledge,
)
from scripts.real_knowledge import REAL_DOCUMENTS

CONTRACT_CODES = {"S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"}
ITEM_NAMES = {
    "S01": "学生证补办",
    "S02": "校园卡补办",
    "S03": "宿舍报修",
    "S04": "请假办理",
    "S05": "奖学金申请",
    "S06": "助学金申请",
    "S07": "转专业咨询",
    "S08": "毕业手续",
}
# 每项事务一个能命中意图、且满足追问规则的问题
QUESTIONS = {
    "S01": "学生证丢了怎么补办？",
    "S02": "校园卡丢了怎么补办？",
    "S03": "宿舍水龙头坏了怎么报修？",
    "S04": "我要请三天病假",
    "S05": "国家奖学金怎么申请？",
    "S06": "助学金申请需要什么条件？",
    "S07": "转专业需要什么条件？",
    "S08": "毕业手续怎么办？",
}
VALID_CARD = (
    '{"title": "事项办理", "summary": "依据知识片段给出的办理说明。", '
    '"eligibility": ["符合办理条件"], "materials": ["所需材料"], '
    '"steps": ["第一步", "第二步"], "location": "以来源通知为准", "deadline": null, '
    '"contacts": [], "warnings": []}'
)
REQUIRED_FIELDS = {
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
    "content",
}


def _seed_items(db_session) -> None:
    for code, name in ITEM_NAMES.items():
        db_session.add(
            ServiceItem(code=code, name=name, category="测试", description="d")
        )
    db_session.commit()


def _item(db_session, code: str) -> ServiceItem:
    item = db_session.scalar(select(ServiceItem).where(ServiceItem.code == code))
    assert item is not None
    return item


def _document_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(SourceDocument))


def _use_llm(db_client: TestClient, llm: MockLLMClient) -> None:
    db_client.app.dependency_overrides[get_llm_client] = lambda: llm


# ── 数据质量 ────────────────────────────────────────────────────────────────


def test_real_knowledge_covers_all_contract_codes():
    assert set(REAL_DOCUMENTS) == CONTRACT_CODES


def test_real_knowledge_entries_have_complete_fields():
    for code, spec in REAL_DOCUMENTS.items():
        assert REQUIRED_FIELDS <= set(spec), code
        assert spec["item_code"] == code
        assert isinstance(spec["publish_date"], date)
        assert isinstance(spec["effective_from"], date)
        assert isinstance(spec["effective_to"], date)
        assert spec["effective_from"] <= spec["effective_to"], code
        assert spec["effective_to"] >= date.today(), f"{code} 的来源已过有效期，需复查更新"
        assert len(spec["content"].strip()) >= 100, f"{code} 正文过短，不足以作为生成依据"


def test_real_knowledge_sources_are_official_and_absolute():
    for code, spec in REAL_DOCUMENTS.items():
        url = spec["official_url"]
        parsed = urlparse(url)
        assert parsed.scheme in {"http", "https"}, code
        assert parsed.netloc.endswith("suda.edu.cn"), f"{code} 来源非学校官方域名：{url}"
        assert DEMO_URL_MARK not in url, code


def test_real_knowledge_status_is_verified():
    assert {spec["status"] for spec in REAL_DOCUMENTS.values()} == {"verified"}


def test_deprecated_s01_and_s07_wording_does_not_return():
    """调研清单已判定 S01/S07 的旧口径不适用现行流程，正文不得回流旧表述。"""
    s01 = REAL_DOCUMENTS["S01"]["content"]
    assert "综合科" not in s01
    assert "5元" in s01 and "只能补办一次" in s01
    assert "jwyy.suda.edu.cn" in s01

    s07 = REAL_DOCUMENTS["S07"]["content"]
    assert "3月中下旬" not in s07 and "4月中旬" not in s07
    assert "6月中下旬" in s07 and "7月初" in s07


def test_independent_college_channel_excluded_from_s02():
    """tec/teccard 属苏州大学应用技术学院（独立学院）口径，不得作为本部办理渠道。"""
    s02 = REAL_DOCUMENTS["S02"]["content"]
    assert "teccard.suda.edu.cn" not in s02
    assert "应用技术学院" not in s02


# ── 导入器行为 ──────────────────────────────────────────────────────────────


def test_loader_requires_seeded_items(db_session):
    with pytest.raises(RuntimeError):
        load_real_knowledge(db_session)


def test_loader_replaces_demo_documents_with_verified_content(db_session):
    _seed_items(db_session)
    item = _item(db_session, "S01")
    db_session.add(
        SourceDocument(
            service_item_id=item.id,
            title="演示占位通知",
            department="学生工作处",
            official_url="https://example.edu.cn/notice/001",
            publish_date=date(2026, 9, 1),
            effective_from=date(2026, 9, 1),
            effective_to=date(2027, 8, 31),
            audience="本科生",
            campus="主校区",
            status=KnowledgeStatus.VERIFIED,
            version="v1.0",
            content="演示正文",
        )
    )
    db_session.commit()

    report = load_real_knowledge(db_session)

    assert report.inserted == len(CONTRACT_CODES)
    assert report.stale_removed == 1
    documents = db_session.scalars(select(SourceDocument)).all()
    assert len(documents) == len(CONTRACT_CODES)
    assert all(DEMO_URL_MARK not in doc.official_url for doc in documents)
    assert all(doc.status is KnowledgeStatus.VERIFIED for doc in documents)
    assert all((doc.content or "").strip() for doc in documents)


def test_loader_is_idempotent(db_session):
    _seed_items(db_session)
    load_real_knowledge(db_session)
    second = load_real_knowledge(db_session)
    assert second.inserted == 0
    assert second.stale_removed == 0
    assert second.updated == len(CONTRACT_CODES)
    assert _document_count(db_session) == len(CONTRACT_CODES)


def test_loader_removes_outdated_review_document(db_session):
    """标题变更后重跑，旧条目（带核验标记）应被清理，不得在同一事项下堆积。"""
    _seed_items(db_session)
    load_real_knowledge(db_session)
    item = _item(db_session, "S01")
    db_session.add(
        SourceDocument(
            service_item_id=item.id,
            title=f"学生证补办指引{REVIEW_TITLE_SUFFIX}",
            department="教务部",
            official_url="https://jwc.suda.edu.cn/old/page.htm",
            publish_date=date(2026, 1, 1),
            effective_from=date(2026, 1, 1),
            effective_to=date(2027, 8, 31),
            audience="本科生",
            campus="各校区",
            status=KnowledgeStatus.VERIFIED,
            version="v2026.01",
            content="旧版正文",
        )
    )
    db_session.commit()

    report = load_real_knowledge(db_session)

    assert report.stale_removed == 1
    assert report.inserted == 0
    assert _document_count(db_session) == len(CONTRACT_CODES)


def test_loader_updates_in_place_when_source_url_changes(db_session):
    """来源 URL 变更（如换用现行文件）时只更新不新增，避免同事项出现两条来源。"""
    _seed_items(db_session)
    load_real_knowledge(db_session)
    item = _item(db_session, "S01")
    document = db_session.scalar(
        select(SourceDocument).where(SourceDocument.service_item_id == item.id)
    )
    document.official_url = "https://www.suda.edu.cn/legacy/bks_xsz.shtml"
    db_session.commit()

    report = load_real_knowledge(db_session)

    assert report.inserted == 0
    assert report.updated == len(CONTRACT_CODES)
    assert _document_count(db_session) == len(CONTRACT_CODES)
    refreshed = db_session.scalar(
        select(SourceDocument).where(SourceDocument.service_item_id == item.id)
    )
    assert refreshed.official_url == REAL_DOCUMENTS["S01"]["official_url"]


# ── 端到端：真实知识下的问答链路 ─────────────────────────────────────────────


@pytest.mark.parametrize("code", sorted(CONTRACT_CODES))
def test_chat_answers_with_real_knowledge(db_client: TestClient, db_session, code):
    _seed_items(db_session)
    load_real_knowledge(db_session)
    _use_llm(db_client, MockLLMClient(default=VALID_CARD))

    resp = db_client.post(
        "/api/chat/messages",
        json={"conversation_id": None, "message": QUESTIONS[code]},
        headers={"X-Session-Token": "real-knowledge-token"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == AnswerStatus.ANSWERED.value, body
    assert body["intent"] == code
    assert body["answer"] is not None
    assert body["sources"], f"{code} 未挂来源"
    source = body["sources"][0]
    assert source["item_code"] == code
    assert source["url"] == REAL_DOCUMENTS[code]["official_url"]
    assert source["status"] == "verified"
    assert source["department"] == REAL_DOCUMENTS[code]["department"]


def test_real_knowledge_content_reaches_the_prompt(db_client: TestClient, db_session):
    """检索到的真实正文必须真的进入提示词，否则生成环节无据可依。

    注：来源 URL 不进提示词——`sources[]` 由后端按契约从数据库映射，
    不采信模型输出（避免模型伪造来源）。
    """
    _seed_items(db_session)
    load_real_knowledge(db_session)
    llm = MockLLMClient(default=VALID_CARD)
    _use_llm(db_client, llm)

    db_client.post(
        "/api/chat/messages",
        json={"conversation_id": None, "message": QUESTIONS["S02"]},
        headers={"X-Session-Token": "real-knowledge-token"},
    )

    prompt = llm.calls[-1][1]
    assert "自助补卡机" in prompt
    assert "65880000" in prompt
    assert "its.suda.edu.cn" not in prompt
