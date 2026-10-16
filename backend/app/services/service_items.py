from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ServiceItem
from app.schemas.service_item import ServiceItemResponse

CONTRACT_ID_MAP = {
    "S01": "student-card",
    "S02": "campus-card",
    "S03": "repair",
    "S04": "leave",
    "S05": "scholarship",
    "S06": "grant",
    "S07": "major-transfer",
    "S08": "graduation",
}

# 契约 §3.1 的展示字段（icon / tone / prompt）为「选返」。
# 数据库列为空时回退到这份缺省表，保证前端拿到的 8 项始终字段齐全；
# 数据库有值时以数据库为准（成员一补数据后无需改代码）。
# icon 取值与前端 `src/data/service-icons.ts` 的渲染结果保持一致（未映射项即 i-doc），
# 避免「后端一个图标、前端渲染另一个」的双来源漂移。
DISPLAY_DEFAULTS: dict[str, dict[str, str]] = {
    "S01": {"icon": "i-id", "tone": "orange", "prompt": "学生证丢了怎么补办？"},
    "S02": {"icon": "i-card", "tone": "blue", "prompt": "校园卡丢了怎么补办？"},
    "S03": {"icon": "i-wrench", "tone": "green", "prompt": "宿舍设施坏了怎么报修？"},
    "S04": {"icon": "i-calendar", "tone": "purple", "prompt": "我要请假，需要办理哪些手续？"},
    "S05": {"icon": "i-award", "tone": "orange", "prompt": "奖学金申请需要准备哪些材料？"},
    "S06": {"icon": "i-doc", "tone": "blue", "prompt": "助学金申请需要满足什么条件？"},
    "S07": {"icon": "i-doc", "tone": "green", "prompt": "转专业需要满足哪些条件？"},
    "S08": {"icon": "i-doc", "tone": "purple", "prompt": "毕业手续要办哪些事项？"},
}

# 契约 §3.1 允许的 tone 取值
ALLOWED_TONES = frozenset({"orange", "blue", "green", "purple"})


def derive_item_id(code: str) -> str:
    return CONTRACT_ID_MAP.get(code, code.lower())


def list_enabled_service_items(session: Session) -> list[ServiceItemResponse]:
    items = session.scalars(
        select(ServiceItem)
        .where(ServiceItem.enabled.is_(True))
        .order_by(ServiceItem.code)
    ).all()
    return [_to_response(item) for item in items]


def _to_response(item: ServiceItem) -> ServiceItemResponse:
    defaults = DISPLAY_DEFAULTS.get(item.code, {})
    return ServiceItemResponse(
        id=derive_item_id(item.code),
        title=item.name,
        description=item.description,
        category=item.category,
        icon=item.icon or defaults.get("icon"),
        tone=item.tone or defaults.get("tone"),
        prompt=item.prompt or defaults.get("prompt"),
    )