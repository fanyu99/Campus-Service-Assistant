"""add source document content

source_documents 原本只有来源元数据（标题/部门/日期/状态），没有正文。
问答链路需要「可依据的片段正文」才能生成结构化答案（实施方案 7.1 / 7.5），
因此补充 content 列。

⚠️ 该列必须回填：检索只把「已核验 + 有效期内 + content 非空」的来源当作生成依据，
   存量库若全部为空会导致问答整体拒答。启用问答前请先执行
   `python scripts/backfill_knowledge_content.py` 或导入真实通知正文。

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-16
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "source_documents",
        sa.Column("content", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("source_documents", "content")
