"""Add nickname column to users table

Revision ID: 0005_nickname
Revises: 0004_interactions
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_nickname"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "nickname")