"""System-owned outbound email service.

Supports both:
1. Platform-level configuration via environment variables
2. Tenant-level configuration via system_settings table
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import smtplib
import ssl
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid

from app.config import get_settings
from app.core.email import force_ipv4, send_smtp_email

logger = logging.getLogger(__name__)


class SystemEmailConfigError(RuntimeError):
    """Raised when system email configuration is missing or invalid."""


@dataclass(slots=True)
class SystemEmailConfig:
    """Resolved system email configuration."""

    from_address: str
    from_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_ssl: bool
    smtp_timeout_seconds: int


@dataclass(slots=True)
class BroadcastEmailRecipient:
    """Prepared broadcast recipient payload."""

    email: str
    subject: str
    body: str


def get_system_email_config() -> SystemEmailConfig:
    """Get platform-level fallback email configuration from environment variables."""
    from app.config import get_settings
    settings = get_settings()
    
    from_address = str(getattr(settings, "SYSTEM_EMAIL_FROM_ADDRESS", "")).strip()
    smtp_host = str(getattr(settings, "SYSTEM_SMTP_HOST", "")).strip()
    smtp_password = str(getattr(settings, "SYSTEM_SMTP_PASSWORD", ""))
    
    if not from_address or not smtp_host or not smtp_password:
        raise SystemEmailConfigError(
            "System email is not configured. Set SYSTEM_EMAIL_FROM_ADDRESS, SYSTEM_SMTP_HOST, and SYSTEM_SMTP_PASSWORD."
        )

    return SystemEmailConfig(
        from_address=from_address,
        from_name=str(getattr(settings, "SYSTEM_EMAIL_FROM_NAME", "Clawith")).strip() or "Clawith",
        smtp_host=smtp_host,
        smtp_port=int(getattr(settings, "SYSTEM_SMTP_PORT", 465)),
        smtp_username=str(getattr(settings, "SYSTEM_SMTP_USERNAME", "")).strip() or from_address,
        smtp_password=smtp_password,
        smtp_ssl=bool(getattr(settings, "SYSTEM_SMTP_SSL", True)),
        smtp_timeout_seconds=max(1, int(getattr(settings, "SYSTEM_SMTP_TIMEOUT_SECONDS", 15))),
    )


async def resolve_email_config_async(db, tenant_id: uuid.UUID | None = None) -> SystemEmailConfig | None:
    """Resolve email configuration by searching in order:
    1. Tenant-specific settings in DB (if tenant_id provided)
    2. Platform-level settings in DB ('system_email_platform')
    3. Environment variables (Settings class)
    """
    from sqlalchemy import select
    from app.models.system_settings import SystemSetting

    # 1. Try tenant-level config
    if tenant_id:
        try:
            config_key = f"system_email_{tenant_id}"
            result = await db.execute(select(SystemSetting).where(SystemSetting.key == config_key))
            setting = result.scalar_one_or_none()
            if setting and setting.value:
                v = setting.value
                if v.get("SYSTEM_EMAIL_FROM_ADDRESS") and v.get("SYSTEM_SMTP_HOST") and v.get("SYSTEM_SMTP_PASSWORD"):
                    return SystemEmailConfig(
                        from_address=str(v.get("SYSTEM_EMAIL_FROM_ADDRESS", "")).strip(),
                        from_name=str(v.get("SYSTEM_EMAIL_FROM_NAME", "Clawith")).strip() or "Clawith",
                        smtp_host=str(v.get("SYSTEM_SMTP_HOST", "")).strip(),
                        smtp_port=int(v.get("SYSTEM_SMTP_PORT", 465)),
                        smtp_username=str(v.get("SYSTEM_SMTP_USERNAME", "")).strip() or str(v.get("SYSTEM_EMAIL_FROM_ADDRESS", "")).strip(),
                        smtp_password=str(v.get("SYSTEM_SMTP_PASSWORD", "")),
                        smtp_ssl=bool(v.get("SYSTEM_SMTP_SSL", True)),
                        smtp_timeout_seconds=max(1, int(v.get("SYSTEM_SMTP_TIMEOUT_SECONDS", 15))),
                    )
        except Exception as e:
            logger.warning(f"Error resolving tenant email config for {tenant_id}: {e}")

    # 2. Try platform-level config in DB
    try:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == "system_email_platform"))
        setting = result.scalar_one_or_none()
        if setting and setting.value:
            v = setting.value
            if v.get("SYSTEM_EMAIL_FROM_ADDRESS") and v.get("SYSTEM_SMTP_HOST") and v.get("SYSTEM_SMTP_PASSWORD"):
                return SystemEmailConfig(
                    from_address=str(v.get("SYSTEM_EMAIL_FROM_ADDRESS", "")).strip(),
                    from_name=str(v.get("SYSTEM_EMAIL_FROM_NAME", "Clawith")).strip() or "Clawith",
                    smtp_host=str(v.get("SYSTEM_SMTP_HOST", "")).strip(),
                    smtp_port=int(v.get("SYSTEM_SMTP_PORT", 465)),
                    smtp_username=str(v.get("SYSTEM_SMTP_USERNAME", "")).strip() or str(v.get("SYSTEM_EMAIL_FROM_ADDRESS", "")).strip(),
                    smtp_password=str(v.get("SYSTEM_SMTP_PASSWORD", "")),
                    smtp_ssl=bool(v.get("SYSTEM_SMTP_SSL", True)),
                    smtp_timeout_seconds=max(1, int(v.get("SYSTEM_SMTP_TIMEOUT_SECONDS", 15))),
                )
    except Exception as e:
        logger.warning(f"Error resolving platform email config: {e}")

    # 3. Fallback to environment variables
    try:
        return get_system_email_config()
    except SystemEmailConfigError:
        return None


async def send_system_email(to: str, subject: str, body: str, tenant_id: uuid.UUID | None = None, db=None) -> None:
    """Send a plain-text system email without blocking the event loop.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        tenant_id: Optional tenant ID to use tenant-specific config
        db: Optional database session
    """
    if not db:
        from app.database import async_session
        async with async_session() as session:
            config = await resolve_email_config_async(session, tenant_id)
    else:
        config = await resolve_email_config_async(db, tenant_id)

    if not config:
        logger.warning(f"System email not configured, skipped sending to {to}")
        return

    await asyncio.to_thread(_send_email_with_config_sync, config, to, subject, body)


def _send_email_with_config_sync(config: SystemEmailConfig, to: str, subject: str, body: str) -> None:
    """Send email with provided config."""
    msg = MIMEMultipart()
    msg["From"] = formataddr((config.from_name, config.from_address))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid()
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
    msg.attach(MIMEText(body, "plain", "utf-8"))

    send_smtp_email(
        host=config.smtp_host,
        port=config.smtp_port,
        user=config.smtp_username,
        password=config.smtp_password,
        from_addr=config.from_address,
        to_addrs=[to],
        msg_string=msg.as_string(),
        use_ssl=config.smtp_ssl,
        timeout=config.smtp_timeout_seconds,
    )


async def send_password_reset_email(
    to: str,
    display_name: str,
    reset_url: str,
    expiry_minutes: int,
    tenant_id: uuid.UUID | None = None,
    db=None,
) -> None:
    """Send a password reset email.

    Args:
        to: Recipient email
        display_name: User display name
        reset_url: Password reset URL
        expiry_minutes: Token expiry time in minutes
        tenant_id: Optional tenant ID for tenant-specific email config
        db: Optional database session
    """
    subject = "Reset your Clawith password"
    body = (
        f"Hello {display_name},\n\n"
        f"We received a request to reset your Clawith password.\n\n"
        f"Reset link: {reset_url}\n\n"
        f"This link expires in {expiry_minutes} minutes. If you did not request this, you can ignore this email."
    )
    await send_system_email(to, subject, body, tenant_id=tenant_id, db=db)


async def deliver_broadcast_emails(recipients: Iterable[BroadcastEmailRecipient]) -> None:
    """Deliver broadcast emails while isolating per-recipient failures."""
    for recipient in recipients:
        try:
            await send_system_email(recipient.email, recipient.subject, recipient.body)
        except Exception as exc:
            logger.warning("Failed to deliver broadcast email to %s: %s", recipient.email, exc)
