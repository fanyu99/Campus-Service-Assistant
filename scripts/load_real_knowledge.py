"""导入真实知识库：用核验过的来源文档替换 S01–S08 的演示占位文档。

背景：
- `seed_demo_data.py` 写入的是 example.edu.cn 占位来源，用于演示各 KnowledgeStatus 分支；
- 2026-10-16 联网核验了苏州大学官方信息（清单见 docs/suda-affairs-research-2026-10.md，
  数据见本目录 real_knowledge.py），本脚本将其作为回答知识库导入 source_documents：
  删除 example.edu.cn 占位文档，按 official_url 幂等 upsert 真实文档（全部 verified、有正文）。

设计要点：
- 幂等：重复执行结果一致；real_knowledge.py 内容更新后重跑即刷新（**以「事项 + 标题」为身份**
  覆盖写，因此改 URL 只更新不新增；标题变更时旧条目按「（核验版）」标记清理，避免重复堆积）；
- 安全：只删除 official_url 含 example.edu.cn 的演示占位文档，以及标题带「（核验版）」
  标记且不在当前清单中的旧条目，不动其它真实文档；
- 有效期至 2027-08-31，下一学年开始前需复查来源并更新（对照调研清单的 ⚠️ 时效项）。

用法（仓库根目录执行，需先跑过 seed_demo_data.py）：
    python scripts/load_real_knowledge.py
"""

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
SCRIPTS_DIR = Path(__file__).resolve().parent
for _path in (str(BACKEND_DIR), str(SCRIPTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sqlalchemy import inspect as sa_inspect  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models import KnowledgeStatus, ServiceItem, SourceDocument  # noqa: E402
from real_knowledge import REAL_DOCUMENTS  # noqa: E402

REQUIRED_TABLES = {"service_items", "source_documents"}
DEMO_URL_MARK = "example.edu.cn"
# 本模块导入的条目统一带该标题后缀，用于识别「本脚本此前导入的旧条目」
REVIEW_TITLE_SUFFIX = "（核验版）"


@dataclass
class LoadReport:
    inserted: int = 0
    updated: int = 0
    stale_removed: int = 0


def load_real_knowledge(session: Session) -> LoadReport:
    inspector = sa_inspect(session.get_bind())
    if not REQUIRED_TABLES <= set(inspector.get_table_names()):
        raise RuntimeError("数据库表结构未就绪，请先执行建库与 alembic upgrade head")

    report = LoadReport()
    try:
        items = {
            item.code: item for item in session.scalars(select(ServiceItem)).all()
        }
        for code, spec in REAL_DOCUMENTS.items():
            item = items.get(code)
            if item is None:
                raise RuntimeError(
                    f"事项 {code} 不存在，请先执行：python scripts/seed_demo_data.py"
                )

            spec_title = spec["title"]
            existing_docs = list(
                session.scalars(
                    select(SourceDocument).where(
                        SourceDocument.service_item_id == item.id
                    )
                ).all()
            )
            for document in existing_docs:
                is_demo = DEMO_URL_MARK in document.official_url
                is_outdated_review = (
                    document.title.endswith(REVIEW_TITLE_SUFFIX)
                    and document.title != spec_title
                )
                if is_demo or is_outdated_review:
                    session.delete(document)
                    report.stale_removed += 1

            payload = {key: value for key, value in spec.items() if key != "item_code"}
            payload["service_item_id"] = item.id
            payload["status"] = KnowledgeStatus(payload["status"])

            existing = session.scalar(
                select(SourceDocument).where(
                    SourceDocument.service_item_id == item.id,
                    SourceDocument.title == payload["title"],
                )
            )
            if existing is None:
                session.add(SourceDocument(**payload))
                report.inserted += 1
            else:
                for key, value in payload.items():
                    setattr(existing, key, value)
                report.updated += 1

        session.commit()
    except Exception:
        session.rollback()
        raise
    return report


def main() -> None:
    engine = create_db_engine()
    try:
        with create_session_factory(engine)() as session:
            try:
                report = load_real_knowledge(session)
            except RuntimeError as exc:
                print(exc)
                raise SystemExit(1) from None
            except Exception as exc:
                print(f"知识库导入失败：{exc.__class__.__name__}，事务已回滚")
                raise SystemExit(1) from None
        print(
            f"真实知识库导入完成：新增 {report.inserted} 条，更新 {report.updated} 条，"
            f"清理占位/过期条目 {report.stale_removed} 条"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
