"""Session management service handling anonymous learner sessions.

Uses cryptographically secure 256-bit tokens, stored only as SHA-256 digests.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from flask import current_app, request, Response, session as flask_session
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


def get_user_session_token(user_id: int, user_email: str) -> str:
    """Generate a deterministic 256-bit token for an authenticated user across all devices."""
    secret = current_app.config.get("SECRET_KEY", "breathquest-user-session-sync")
    return hmac.new(
        secret.encode("utf-8"),
        f"user_session:{user_id}:{user_email.strip().lower()}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_current_session() -> StudentSession | None:
    """Retrieve the active student session from authenticated user or request cookie."""
    # 1. Check if user is authenticated in Flask session (cross-device sync)
    user_id = flask_session.get("user_id")
    if user_id:
        from app.models.user import User

        user = db.session.get(User, user_id)
        if user:
            user_raw_token = get_user_session_token(user.id, user.email)
            user_token_hash = hash_token(user_raw_token)
            session_obj = db.session.execute(
                select(StudentSession).where(StudentSession.token_hash == user_token_hash)
            ).scalar_one_or_none()
            if session_obj and not session_obj.is_expired:
                return session_obj

            # If not yet bound to deterministic hash, resolve via get_or_create_session
            bound_session, _, _ = get_or_create_session()
            return bound_session

    # 2. Anonymous / Guest session lookup from cookie
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
    """Retrieve existing active session from user account or request, or create a fresh one.

    Returns:
        tuple of (session_object, raw_token, is_new_session)
    """
    now = datetime.now(timezone.utc)
    lifetime = current_app.config.get("PERMANENT_SESSION_LIFETIME")
    expires_at = now + lifetime if lifetime else now

    # 1. Authenticated User flow (Syncs laptop, iPad, and phones seamlessly)
    user_id = flask_session.get("user_id")
    if user_id:
        from app.models.user import User

        user = db.session.get(User, user_id)
        if user:
            user_raw_token = get_user_session_token(user.id, user.email)
            user_token_hash = hash_token(user_raw_token)

            # 1a. Check if already bound
            session_obj = db.session.execute(
                select(StudentSession).where(StudentSession.token_hash == user_token_hash)
            ).scalar_one_or_none()
            if session_obj:
                session_obj.last_active_at = now
                if lifetime:
                    session_obj.expires_at = expires_at
                if not session_obj.nickname and user.student_id:
                    session_obj.nickname = user.student_id
                db.session.commit()
                return session_obj, user_raw_token, False

            # 1b. Check if user has an existing session from another device (by nickname)
            candidate_session = None
            if user.student_id:
                candidate_session = db.session.execute(
                    select(StudentSession)
                    .where(StudentSession.nickname == user.student_id)
                    .order_by(StudentSession.last_active_at.desc())
                ).scalars().first()

            # 1c. Check if incoming request cookie has an active session with runs
            if not candidate_session:
                cookie_name = current_app.config.get("LEARNER_COOKIE_NAME", "bq_learner")
                raw_token = request.cookies.get(cookie_name)
                if raw_token and len(raw_token) >= 20:
                    digest = hash_token(raw_token)
                    cookie_session = db.session.execute(
                        select(StudentSession).where(StudentSession.token_hash == digest)
                    ).scalar_one_or_none()
                    if cookie_session:
                        candidate_session = cookie_session

            # 1d. If no candidate, look for the most recent orphaned session that has gameplay runs
            if not candidate_session:
                candidate_session = db.session.execute(
                    select(StudentSession)
                    .filter(StudentSession.runs.any())
                    .order_by(StudentSession.last_active_at.desc())
                ).scalars().first()

            if candidate_session:
                # Bind this existing session to canonical user hash
                candidate_session.token_hash = user_token_hash
                candidate_session.nickname = user.student_id or user.name
                candidate_session.last_active_at = now
                if lifetime:
                    candidate_session.expires_at = expires_at
                db.session.commit()
                logger.info(
                    "Migrated existing student session %s to canonical user %s (%s)",
                    candidate_session.id,
                    user.id,
                    user.email,
                )
                return candidate_session, user_raw_token, False

            # 1e. Fresh canonical session
            new_session = StudentSession(
                token_hash=user_token_hash,
                nickname=user.student_id or user.name,
                created_at=now,
                last_active_at=now,
                expires_at=expires_at,
            )
            db.session.add(new_session)
            db.session.commit()
            logger.info("Created new canonical student session id=%s for user %s", new_session.id, user.id)
            return new_session, user_raw_token, True

    # 2. Guest / Anonymous Learner flow
    cookie_name = current_app.config.get("LEARNER_COOKIE_NAME", "bq_learner")
    raw_token = request.cookies.get(cookie_name)

    if raw_token and len(raw_token) >= 20:
        digest = hash_token(raw_token)
        session_obj = db.session.execute(
            select(StudentSession).where(StudentSession.token_hash == digest)
        ).scalar_one_or_none()

        if session_obj and not session_obj.is_expired:
            session_obj.last_active_at = now
            db.session.commit()
            return session_obj, raw_token, False

    # Create fresh anonymous session
    new_raw_token = generate_raw_token()
    token_hash = hash_token(new_raw_token)
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
