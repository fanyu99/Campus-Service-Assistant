from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.service_item import ServiceItemResponse
from app.services.service_items import list_enabled_service_items

router = APIRouter(prefix="/api")


@router.get("/service-items", response_model=list[ServiceItemResponse])
def get_service_items(db: Session = Depends(get_db)) -> list[ServiceItemResponse]:
    return list_enabled_service_items(db)