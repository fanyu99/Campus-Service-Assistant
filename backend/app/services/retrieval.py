"""知识检索与依据判断（实施方案 7.4 / 7.5）。

AgentArts 知识库尚未搭建，检索暂由后端基于 source_documents 元数据完成：
- 按事项过滤，用校区/适用对象做「软过滤」（有匹配则收窄，无匹配则保留全部，避免因数据缺失误拒答）；
- 只有「已核验 + 在有效期内 + 有正文」的来源才可作为生成依据（准确优先，过期/草稿不作为唯一依据）；
- 存在冲突来源时不给确定结论（conflict 态）。
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.sanitize import is_safe_source_url
from app.models import AnswerStatus, KnowledgeStatus, ServiceItem, SourceDocument
from app.schemas.chat import ChatContext, ChatSource

MAX_SNIPPETS = 5

# 学生类型取值口径映射：契约示例用英文（undergraduate），而 audience 是中文描述
STUDENT_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "undergraduate": ("本科",),
    "graduate": ("研究生", "硕士"),
    "postgraduate": ("研究生", "硕士"),
    "doctor": ("博士",),
    "phd": ("博士",),
}

# 不可作为生成依据、但可回传给前端做风险提示的状态
UNAVAILABLE_STATUSES = (KnowledgeStatus.EXPIRED, KnowledgeStatus.DRAFT)


def _audience_matches(student_type: str, audience: str) -> bool:
    keywords = STUDENT_TYPE_KEYWORDS.get(student_type.strip().lower(), (student_type,))
    return any(keyword in audience for keyword in keywords)


@dataclass(frozen=True)
class RetrievalOutcome:
    status: AnswerStatus
    documents: tuple[SourceDocument, ...]
    sources: tuple[ChatSource, ...]
    has_unverified: bool


def _to_source(document: SourceDocument, item_code: str) -> ChatSource:
    return ChatSource(
        title=document.title,
        department=document.department,
        published_at=document.publish_date.isoformat(),
        url=document.official_url,
        item_code=item_code,
        status=document.status.value,
    )


def _in_effect(document: SourceDocument, today: date) -> bool:
    return document.effective_from <= today <= document.effective_to


def _is_citable(document: SourceDocument) -> bool:
    """来源链接必须是 http/https 绝对地址，否则无法对外引用（契约 §3.2、OWASP A08）。"""
    return is_safe_source_url(document.official_url)


def _apply_context(
    documents: list[SourceDocument], context: ChatContext | None
) -> list[SourceDocument]:
    """校区/学生类型按「软过滤」处理：命中则收窄，未命中则维持原集合。"""
    if context is None:
        return documents
    narrowed = documents
    if context.campus:
        matched = [doc for doc in narrowed if doc.campus == context.campus]
        if matched:
            narrowed = matched
    if context.student_type:
        matched = [
            doc
            for doc in narrowed
            if _audience_matches(context.student_type, doc.audience)
        ]
        if matched:
            narrowed = matched
    return narrowed


def retrieve_documents(
    session: Session, intent_code: str, context: ChatContext | None = None
) -> RetrievalOutcome:
    item = session.scalar(select(ServiceItem).where(ServiceItem.code == intent_code))
    if item is None:
        return RetrievalOutcome(AnswerStatus.INSUFFICIENT_EVIDENCE, (), (), False)

    documents = list(
        session.scalars(
            select(SourceDocument)
            .where(SourceDocument.service_item_id == item.id)
            .order_by(SourceDocument.publish_date.desc())
        ).all()
    )
    documents = _apply_context(documents, context)
    # 链接不可引用的来源一律剔除：既不能作为生成依据，也不能出现在 sources 里
    documents = [doc for doc in documents if _is_citable(doc)]

    conflicts = [doc for doc in documents if doc.status is KnowledgeStatus.CONFLICT]
    if conflicts:
        selected = conflicts[:MAX_SNIPPETS]
        return RetrievalOutcome(
            AnswerStatus.CONFLICT,
            tuple(selected),
            tuple(_to_source(doc, intent_code) for doc in selected),
            True,
        )

    today = date.today()
    grounded = [
        doc
        for doc in documents
        if doc.status is KnowledgeStatus.VERIFIED
        and _in_effect(doc, today)
        and (doc.content or "").strip()
    ]
    if grounded:
        selected = grounded[:MAX_SNIPPETS]
        has_unverified = len(grounded) < len(documents)
        return RetrievalOutcome(
            AnswerStatus.ANSWERED,
            tuple(selected),
            tuple(_to_source(doc, intent_code) for doc in selected),
            has_unverified,
        )

    # 无已核验依据（无来源 / 仅草稿 / 仅过期）→ 拒答，不编造流程。
    # 同时把「存在但不可用」的来源回传，前端可据此提示「资料可能已失效」
    # （实施方案测试用例 4：不输出确定流程，但要提示资料可能已经失效）。
    unavailable = [doc for doc in documents if doc.status in UNAVAILABLE_STATUSES]
    selected = unavailable[:MAX_SNIPPETS]
    return RetrievalOutcome(
        AnswerStatus.INSUFFICIENT_EVIDENCE,
        (),
        tuple(_to_source(doc, intent_code) for doc in selected),
        bool(documents),
    )
