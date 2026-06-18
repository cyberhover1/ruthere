"""Activity (活跃度) service hooks.

M1 only defines the placeholder called on login. The real implementation
(storing activity_reports, setting value to 100) lands in M3.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def reset_activity_for_user(user_id: int, db: Session) -> None:
    """Reset a user's activity level to full (100) on login / poke.

    M1 placeholder — does not touch any table yet. Implemented in M3.
    """
    logger.info("TODO(M3): reset activity for user_id=%s (placeholder)", user_id)
