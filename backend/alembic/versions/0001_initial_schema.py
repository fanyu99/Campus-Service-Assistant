"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_items")),
        sa.UniqueConstraint("code", name=op.f("uq_service_items_code")),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_item_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=128), nullable=False),
        sa.Column("official_url", sa.String(length=512), nullable=False),
        sa.Column("publish_date", sa.Date(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=False),
        sa.Column("audience", sa.String(length=128), nullable=False),
        sa.Column("campus", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "verified", "expired", "conflict"),
            nullable=False,
        ),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("reviewed_at", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["service_item_id"],
            ["service_items.id"],
            name=op.f("fk_source_documents_service_items_id"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "effective_to >= effective_from",
            name=op.f("ck_source_documents_effective_range"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'verified', 'expired', 'conflict')",
            name=op.f("ck_source_documents_status_values"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_documents")),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index(
        op.f("ix_source_documents_service_item_id"),
        "source_documents",
        ["service_item_id"],
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("last_intent", sa.String(length=8), nullable=True),
        sa.Column(
            "result_status",
            sa.Enum(
                "answered",
                "need_clarification",
                "unsupported",
                "insufficient_evidence",
                "conflict",
                "service_error",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["last_intent"],
            ["service_items.code"],
            name=op.f("fk_conversations_service_items_code"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "result_status IN ('answered', 'need_clarification', 'unsupported', "
            "'insufficient_evidence', 'conflict', 'service_error')",
            name=op.f("ck_conversations_result_status_values"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index(
        op.f("ix_conversations_last_message_at"),
        "conversations",
        ["last_message_at"],
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column(
            "reason_code",
            sa.Enum("SOURCE_ERROR", "INCOMPLETE_STEPS", "OUTDATED_CONTENT", "OTHER"),
            nullable=True,
        ),
        sa.Column("comment", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_feedback_conversations_id"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "reason_code IS NULL OR reason_code IN "
            "('SOURCE_ERROR', 'INCOMPLETE_STEPS', 'OUTDATED_CONTENT', 'OTHER')",
            name=op.f("ck_feedback_reason_code_values"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index(
        op.f("ix_feedback_conversation_id"),
        "feedback",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_conversation_id"), table_name="feedback")
    op.drop_table("feedback")
    op.drop_index(op.f("ix_conversations_last_message_at"), table_name="conversations")
    op.drop_table("conversations")
    op.drop_index(
        op.f("ix_source_documents_service_item_id"), table_name="source_documents"
    )
    op.drop_table("source_documents")
    op.drop_table("service_items")