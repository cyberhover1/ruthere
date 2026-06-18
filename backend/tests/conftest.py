"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Force a safe in-process config before any app import happens.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("RESEND_API_KEY", "")
