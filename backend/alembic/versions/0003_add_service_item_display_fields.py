"""add service item display fields

给 service_items 补充契约 §3.1 的展示字段（icon / tone / prompt，均为「选返」，
因此一律 nullable，旧数据与旧响应保持兼容）。

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-16
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_items",
        sa.Column("icon", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "service_items",
        sa.Column("tone", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "service_items",
        sa.Column("prompt", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_items", "prompt")
    op.drop_column("service_items", "tone")
    op.drop_column("service_items", "icon")
