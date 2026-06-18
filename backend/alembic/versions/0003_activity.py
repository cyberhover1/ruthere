"""activity: activity_reports

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("friend_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_reported_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reported_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_offline", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "friend_id", name="uq_activity_reports_user_friend"),
    )
    op.create_index("ix_activity_reports_user_id", "activity_reports", ["user_id"])
    op.create_index("ix_activity_reports_friend_id", "activity_reports", ["friend_id"])


def downgrade() -> None:
    op.drop_index("ix_activity_reports_friend_id", table_name="activity_reports")
    op.drop_index("ix_activity_reports_user_id", table_name="activity_reports")
    op.drop_table("activity_reports")
