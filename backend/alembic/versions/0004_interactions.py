"""interactions: checkins, pokes

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_checkins_user_id", "checkins", ["user_id"])

    op.create_table(
        "pokes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pokes_from_user_id", "pokes", ["from_user_id"])
    op.create_index("ix_pokes_to_user_id", "pokes", ["to_user_id"])


def downgrade() -> None:
    op.drop_index("ix_pokes_to_user_id", table_name="pokes")
    op.drop_index("ix_pokes_from_user_id", table_name="pokes")
    op.drop_table("pokes")
    op.drop_index("ix_checkins_user_id", table_name="checkins")
    op.drop_table("checkins")
