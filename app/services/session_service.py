"""Session management service handling anonymous learner sessions.

Uses cryptographically secure 256-bit tokens, stored only as SHA-256 digests.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from flask import current_app, request, Response
from sqlalchemy import select
from app.extensions import db
from app.models.session import StudentSession

logger = logging.getLogger(__name__)


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 digest of a raw session token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_raw_token() -> str:
    """Generate a cryptographically secure 256-bit random token."""
    return secrets.token_urlsafe(32)


def get_current_session() -> StudentSession | None:
    """Retrieve the active student session from the request cookie, if valid and unexpired."""
    cookie_name = current_app.config.get("LEARNER_COOKIE_NAME", "bq_learner")
    raw_token = request.cookies.get(cookie_name)
    if not raw_token or len(raw_token) < 20:
        return None

    digest = hash_token(raw_token)
    session_obj = db.session.execute(
        select(StudentSession).where(StudentSession.token_hash == digest)
    ).scalar_one_or_none()

    if session_obj is None:
        return None

    if session_obj.is_expired:
        logger.info("Session %s has expired", session_obj.id)
        return None

    return session_obj


def get_or_create_session() -> tuple[StudentSession, str, bool]:
    """Retrieve existing active session from request, or create a fresh one.

    Returns:
        tuple of (session_object, raw_token, is_new_session)
    """
    cookie_name = current_app.config.get("LEARNER_COOKIE_NAME", "bq_learner")
    raw_token = request.cookies.get(cookie_name)

    if raw_token and len(raw_token) >= 20:
        digest = hash_token(raw_token)
        session_obj = db.session.execute(
            select(StudentSession).where(StudentSession.token_hash == digest)
        ).scalar_one_or_none()

        if session_obj and not session_obj.is_expired:
            # Touch last active
            session_obj.last_active_at = datetime.now(timezone.utc)
            db.session.commit()
            return session_obj, raw_token, False

    # Create a fresh anonymous session
    new_raw_token = generate_raw_token()
    token_hash = hash_token(new_raw_token)
    now = datetime.now(timezone.utc)
    lifetime = current_app.config.get("PERMANENT_SESSION_LIFETIME")
    expires_at = now + lifetime

    new_session = StudentSession(
        token_hash=token_hash,
        created_at=now,
        last_active_at=now,
        expires_at=expires_at,
    )
    db.session.add(new_session)
    db.session.commit()

    logger.info("Created new anonymous student session id=%s", new_session.id)
    return new_session, new_raw_token, True


def set_session_cookie(response: Response, raw_token: str) -> None:
    """Attach the HttpOnly session token cookie to the response."""
    cookie_name = current_app.config.get("LEARNER_COOKIE_NAME", "bq_learner")
    lifetime = current_app.config.get("PERMANENT_SESSION_LIFETIME")
    max_age = int(lifetime.total_seconds()) if lifetime else 3600 * 24 * 30
    secure = current_app.config.get("SESSION_COOKIE_SECURE", False)
    samesite = current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax")
    httponly = current_app.config.get("SESSION_COOKIE_HTTPONLY", True)

    response.set_cookie(
        key=cookie_name,
        value=raw_token,
        max_age=max_age,
        httponly=httponly,
        samesite=samesite,
        secure=secure,
        path="/",
    )
