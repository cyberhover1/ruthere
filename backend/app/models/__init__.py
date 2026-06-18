"""ORM models placeholder.

Concrete models (users, devices, friendships, activity_reports, ...) land in
M1–M4. Importing Base here lets Alembic's `target_metadata` discover future
models via `from app.models import *`.
"""

from app.db.base import Base  # noqa: F401
