"""Declarative base shared by all ORM models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All models subclass this so Alembic can autogenerate migrations."""
