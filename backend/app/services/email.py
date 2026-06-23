"""Email verification via Resend.

Raises a [EmailSendError] when the API key is missing or Resend rejects the
request, so the caller can surface a meaningful error to the user instead of
silently pretending the email was sent.
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when a verification email cannot be sent."""


def send_verification_email(email: str, code: str) -> None:
    """Send a 6-digit verification code to `email` via Resend.

    Raises EmailSendError if RESEND_API_KEY is unset or the Resend API call
    fails — the caller should catch this and return an error to the client.
    """
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — cannot send email to %s", email)
        raise EmailSendError("邮件服务未配置（RESEND_API_KEY 为空），无法发送验证码")

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
    try:
        resend.Emails.send(params)
        logger.info("Verification email sent to %s", email)
    except Exception as e:
        logger.error("Resend send failed for %s: %s", email, e)
        raise EmailSendError(f"验证码邮件发送失败：{e}") from e
