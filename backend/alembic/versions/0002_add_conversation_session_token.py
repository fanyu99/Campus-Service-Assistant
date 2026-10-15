"""add conversation session_token

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("session_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_conversations_session_token"),
        "conversations",
        ["session_token"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_conversations_session_token"), table_name="conversations")
    op.drop_column("conversations", "session_token")