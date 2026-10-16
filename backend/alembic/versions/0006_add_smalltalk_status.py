"""add smalltalk answer status

问题三：非事项问题不再机械回复「暂不支持」。新增 smalltalk 状态
（寒暄 / 与校园事务无关的闲聊 / 表述不清时的引导对话），
conversations.result_status 的枚举与 CheckConstraint 同步加入该取值。

约束（修复方案 3.4）：smalltalk 不得输出政策、时间、地点、电话与办理流程。
CheckConstraint 修改用 batch 模式：MySQL 直接 ALTER，SQLite 走表重建，
两种库形态一致（存量数据无需迁移，枚举只是扩值）。

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-16
"""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

_STATUS_VALUES = (
    "answered",
    "need_clarification",
    "unsupported",
    "insufficient_evidence",
    "conflict",
    "service_error",
    "smalltalk",
)
_OLD_STATUS_VALUES = _STATUS_VALUES[:6]
# batch 模式会对传入名再套一次 naming convention（ck_<table>_<name>），
# 这里传 models/conversation.py CheckConstraint 的原始名，展开后即 0001 的落库名
_CHECK_NAME = "result_status_values"


def _check_sql(values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"result_status IN ({quoted})"


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.alter_column(
            "result_status",
            existing_type=sa.Enum(*_OLD_STATUS_VALUES),
            type_=sa.Enum(*_STATUS_VALUES),
            existing_nullable=False,
        )
        batch_op.drop_constraint(_CHECK_NAME, type_="check")
        batch_op.create_check_constraint(_CHECK_NAME, _check_sql(_STATUS_VALUES))


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_constraint(_CHECK_NAME, type_="check")
        batch_op.create_check_constraint(_CHECK_NAME, _check_sql(_OLD_STATUS_VALUES))
        batch_op.alter_column(
            "result_status",
            existing_type=sa.Enum(*_STATUS_VALUES),
            type_=sa.Enum(*_OLD_STATUS_VALUES),
            existing_nullable=False,
        )
