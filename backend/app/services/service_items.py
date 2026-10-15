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


def derive_item_id(code: str) -> str:
    return CONTRACT_ID_MAP.get(code, code.lower())


def list_enabled_service_items(session: Session) -> list[ServiceItemResponse]:
    items = session.scalars(
        select(ServiceItem)
        .where(ServiceItem.enabled.is_(True))
        .order_by(ServiceItem.code)
    ).all()
    return [
        ServiceItemResponse(
            id=derive_item_id(item.code),
            title=item.name,
            description=item.description,
            category=item.category,
        )
        for item in items
    ]