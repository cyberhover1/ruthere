"""Email verification via Resend.

If `RESEND_API_KEY` is empty the send is skipped (logged), so local dev without
a key can still exercise the register/verify flow. Tests monkeypatch
`send_verification_email` to avoid real network calls.
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(email: str, code: str) -> None:
    """Send a 6-digit verification code to `email` via Resend."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping email send to %s (code=%s)", email, code)
        return

    # Imported lazily so tests without a key don't require the SDK at import time.
    import resend  # type: ignore[import-not-found]

    resend.api_key = settings.resend_api_key
    params: resend.Emails.SendParams = {
        "from": settings.resend_from_email,
        "to": [email],
        "subject": "【安心圈】邮箱验证码",
        "html": (
            f"<p>你的安心圈验证码是：</p>"
            f"<p style='font-size:28px;font-weight:bold;letter-spacing:4px'>{code}</p>"
            f"<p>验证码 {settings.email_code_expire_minutes} 分钟内有效，请勿泄露给他人。</p>"
        ),
    }
    resend.Emails.send(params)
    logger.info("Verification email sent to %s", email)
