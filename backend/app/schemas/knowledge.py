from datetime import date

from pydantic import BaseModel, Field

from app.models.source_document import KnowledgeStatus


class KnowledgeSourceResponse(BaseModel):
    """契约 §4.6 的知识来源条目。

    ``id`` / ``service_item_id`` 按契约示例以字符串返回；日期一律 ``YYYY-MM-DD``。
    """

    id: str
    service_item_id: str
    item_code: str | None = None
    title: str
    department: str
    official_url: str
    publish_date: date
    effective_from: date
    effective_to: date
    audience: str
    campus: str
    status: KnowledgeStatus
    version: str
    reviewed_at: date | None = None


class KnowledgeSourceListResponse(BaseModel):
    sources: list[KnowledgeSourceResponse]
    total: int = Field(ge=0)
