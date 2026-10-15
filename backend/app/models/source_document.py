import enum
from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, enum_values


class KnowledgeStatus(str, enum.Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    EXPIRED = "expired"
    CONFLICT = "conflict"


class SourceDocument(Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        CheckConstraint("effective_to >= effective_from", name="effective_range"),
        CheckConstraint(
            "status IN ('draft', 'verified', 'expired', 'conflict')",
            name="status_values",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_item_id: Mapped[int] = mapped_column(
        ForeignKey("service_items.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(128))
    official_url: Mapped[str] = mapped_column(String(512))
    publish_date: Mapped[date] = mapped_column(Date)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date] = mapped_column(Date)
    audience: Mapped[str] = mapped_column(String(128))
    campus: Mapped[str] = mapped_column(String(64))
    status: Mapped[KnowledgeStatus] = mapped_column(
        Enum(KnowledgeStatus, values_callable=enum_values), default=KnowledgeStatus.DRAFT
    )
    version: Mapped[str] = mapped_column(String(32))
    reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    service_item: Mapped["ServiceItem"] = relationship(back_populates="documents")