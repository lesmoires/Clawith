"""Email verification token lifecycle helpers."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.core.events import get_redis

# Key prefixes for Redis
TOKEN_PREFIX = "email_verify:token:"
USER_PREFIX = "email_verify:user:"


def _hash_token(token: str) -> str:
    """Hash a raw verification token before persistence or lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_email_verification_token(user_id: uuid.UUID, email: str) -> tuple[str, datetime]:
    """Create a new 6-digit email verification code and store in Redis."""
    redis = await get_redis()
    user_key = f"{USER_PREFIX}{user_id}"

    # Invalidate previous code for this user if exists
    old_code_hash = await redis.get(user_key)
    if old_code_hash:
        await redis.delete(f"{TOKEN_PREFIX}{old_code_hash}")

    # Generate a random 6-digit code
    raw_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    code_hash = _hash_token(raw_code)

    now = datetime.now(timezone.utc)
    expiry_minutes = get_settings().EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
    expires_at = now + timedelta(minutes=expiry_minutes)

    # Store the new code with user_id and email
    token_key = f"{TOKEN_PREFIX}{code_hash}"
    ttl_seconds = int(expiry_minutes * 60)

    # Store as JSON with user_id and email
    import json
    token_data = json.dumps({"user_id": str(user_id), "email": email})

    async with redis.pipeline(transaction=True) as pipe:
        pipe.setex(token_key, ttl_seconds, token_data)
        pipe.setex(user_key, ttl_seconds, code_hash)
        await pipe.execute()

    return raw_code, expires_at


async def build_email_verification_url(base_url: str, raw_token: str) -> str:
    """Build the user-facing verification URL. Note: now uses 6-digit code."""
    base = base_url.strip().rstrip("/")
    return f"{base}/verify-email?code={raw_token}"


async def consume_email_verification_token(raw_token: str) -> dict | None:
    """Load a valid verification code from Redis and mark it used (by deleting)."""
    import json

    redis = await get_redis()
    token_hash = _hash_token(raw_token)
    token_key = f"{TOKEN_PREFIX}{token_hash}"

    token_data_str = await redis.get(token_key)
    if not token_data_str:
        return None

    try:
        token_data = json.loads(token_data_str)
        user_id = uuid.UUID(token_data["user_id"])
        email = token_data["email"]
    except (json.JSONDecodeError, KeyError, ValueError):
        return None

    user_key = f"{USER_PREFIX}{user_id}"

    # Atomic delete to ensure single-use
    async with redis.pipeline(transaction=True) as pipe:
        pipe.delete(token_key)
        pipe.delete(user_key)
        await pipe.execute()

    return {"user_id": user_id, "email": email}


async def send_verification_email(
    to: str,
    display_name: str,
    verification_code: str,
    expiry_minutes: int,
    tenant_id: uuid.UUID | None = None,
) -> None:
    """Send an email verification code."""
    from app.services.system_email_service import send_system_email

    await send_system_email(
        to,
        "Verify your Clawith email address",
        (
            f"Hello {display_name},\n\n"
            f"Welcome to Clawith! Please use the following 6-digit code to verify your email address:\n\n"
            f"Verification code: {verification_code}\n\n"
            f"This code expires in {expiry_minutes} minutes. "
            f"If you did not create an account, you can ignore this email."
        ),
        tenant_id=tenant_id,
    )
