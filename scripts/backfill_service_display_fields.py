"""回填 service_items 的展示字段（icon / tone / prompt）。

背景：
- 迁移 0003 给 service_items 增加了契约 §3.1 的展示字段（icon / tone / prompt），
  列为可空，历史数据不会自动带上值；
- 后端 `app/services/service_items.py` 的 `DISPLAY_DEFAULTS` 已能兜底返回这 3 个字段，
  本脚本用于把缺省值**落库**（数据驱动），已有值不覆盖，可重复执行。

知识正文不在这里回填：S01–S08 的来源与正文由 `scripts/load_real_knowledge.py`
从 `scripts/real_knowledge.py`（核验版，2026-10-16）导入。

用法（仓库根目录执行，需先跑过 seed_demo_data.py）：
    python scripts/backfill_service_display_fields.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models import ServiceItem  # noqa: E402
from app.services.service_items import DISPLAY_DEFAULTS  # noqa: E402

DISPLAY_FIELDS = ("icon", "tone", "prompt")


def backfill_display_fields(session) -> int:
    """把缺省展示字段写入为空的列，返回被更新的条数。"""
    items = list(session.scalars(select(ServiceItem)).all())
    if not items:
        return 0
    by_code = {item.code: item for item in items}
    updated = 0
    for code, values in DISPLAY_DEFAULTS.items():
        item = by_code.get(code)
        if item is None:
            continue
        changed = False
        for field in DISPLAY_FIELDS:
            if getattr(item, field) is None:
                setattr(item, field, values[field])
                changed = True
        if changed:
            updated += 1
    return updated


def main() -> None:
    engine = create_db_engine(get_settings().database_url)
    try:
        with create_session_factory(engine)() as session:
            updated = backfill_display_fields(session)
            if updated == 0:
                print("未找到可回填的事项，请先执行：python scripts/seed_demo_data.py")
                return
            session.commit()
        print(f"展示字段回填完成：更新 {updated} 项")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
