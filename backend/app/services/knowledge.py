"""知识来源查询（契约 §4.6）。

只读接口：供知识维护者与后续「知识来源」页查看库内来源的核验状态、有效期与适用范围。
纯查询、无 PII；``item_code`` 通过关联 ``service_items.code`` 过滤。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeStatus, ServiceItem, SourceDocument
from app.schemas.knowledge import KnowledgeSourceListResponse, KnowledgeSourceResponse


def list_source_documents(
    session: Session,
    status: KnowledgeStatus | None = None,
    item_code: str | None = None,
) -> KnowledgeSourceListResponse:
    statement = (
        select(SourceDocument, ServiceItem.code)
        .join(ServiceItem, SourceDocument.service_item_id == ServiceItem.id)
        .order_by(SourceDocument.publish_date.desc(), SourceDocument.id.desc())
    )
    if status is not None:
        statement = statement.where(SourceDocument.status == status)
    if item_code:
        statement = statement.where(ServiceItem.code == item_code)

    rows = session.execute(statement).all()
    sources = [
        KnowledgeSourceResponse(
            id=str(document.id),
            service_item_id=str(document.service_item_id),
            item_code=code,
            title=document.title,
            department=document.department,
            official_url=document.official_url,
            publish_date=document.publish_date,
            effective_from=document.effective_from,
            effective_to=document.effective_to,
            audience=document.audience,
            campus=document.campus,
            status=document.status,
            version=document.version,
            reviewed_at=document.reviewed_at,
        )
        for document, code in rows
    ]
    return KnowledgeSourceListResponse(sources=sources, total=len(sources))
