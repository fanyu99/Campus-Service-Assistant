from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import KnowledgeStatus
from app.schemas.knowledge import KnowledgeSourceListResponse
from app.services.knowledge import list_source_documents

router = APIRouter(prefix="/api")


@router.get("/knowledge/sources", response_model=KnowledgeSourceListResponse)
def get_knowledge_sources(
    status: Annotated[KnowledgeStatus | None, Query()] = None,
    item_code: Annotated[str | None, Query()] = None,
    db: Session = Depends(get_db),
) -> KnowledgeSourceListResponse:
    # status 取值非法时由 FastAPI 枚举校验直接返回 422（契约 §4.6）
    return list_source_documents(db, status, item_code)
