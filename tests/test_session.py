"""Tests for anonymous learner session lifecycle, CSRF, security, and cookies."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from flask import Flask
from sqlalchemy import select
from app import create_app
from app.extensions import db
from app.models.session import StudentSession
from app.services.session_service import hash_token
from tests.conftest import extract_csrf_token


def test_session_start_requires_csrf_when_enabled(tmp_path):
    """CSRF protection must reject POST /session/start without a valid CSRF token."""
    db_file = tmp_path / "csrf_test.db"
    csrf_app = create_app({
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "WTF_CSRF_ENABLED": True,
    })

    with csrf_app.app_context():
        db.create_all()
        client = csrf_app.test_client()

        # 1. Post without CSRF token -> 400 Bad Request
        res_no_csrf = client.post("/session/start")
        assert res_no_csrf.status_code == 400

        # 2. Post with invalid CSRF token -> 400 Bad Request
        res_bad_csrf = client.post("/session/start", data={"csrf_token": "invalid_fake_token"})
        assert res_bad_csrf.status_code == 400

        # 3. GET / to obtain genuine CSRF token from page
        home_res = client.get("/")
        assert home_res.status_code == 200
        csrf_token = extract_csrf_token(home_res.get_data(as_text=True))
        assert csrf_token is not None

        # 4. POST with valid CSRF token -> 302 redirect to /ward
        start_res = client.post("/session/start", data={"csrf_token": csrf_token})
        assert start_res.status_code == 302
        assert start_res.headers["Location"].endswith("/ward")

        # Verify session record created in DB with hashed token (not raw token)
        cookie_header = start_res.headers.get("Set-Cookie")
        assert "bq_learner=" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=Lax" in cookie_header

        sessions = db.session.execute(select(StudentSession)).scalars().all()
        assert len(sessions) == 1
        stored_hash = sessions[0].token_hash
        # Ensure stored hash is a 64-character SHA-256 string
        assert len(stored_hash) == 64
        # Stored hash must NOT equal raw cookie token
        raw_cookie_val = [c.split(";")[0].split("=")[1] for c in cookie_header.split(",") if "bq_learner=" in c][0]
        assert stored_hash != raw_cookie_val
        assert stored_hash == hash_token(raw_cookie_val)


def test_session_reuse_on_subsequent_start(client, app):
    """Subsequent session start request with a valid cookie reuses the existing session."""
    with app.app_context():
        # Start initial session
        res1 = client.post("/session/start")
        assert res1.status_code == 302

        sessions_count_1 = len(db.session.execute(select(StudentSession)).scalars().all())
        assert sessions_count_1 == 1

        # Second start with same client (cookie preserved)
        res2 = client.post("/session/start")
        assert res2.status_code == 302

        sessions_count_2 = len(db.session.execute(select(StudentSession)).scalars().all())
        assert sessions_count_2 == 1  # No duplicate created


def test_expired_or_malformed_token_handling(client, app):
    """Expired or malformed cookie token cannot access or revive old session."""
    with app.app_context():
        # Insert an already-expired session
        expired_sess = StudentSession(
            token_hash=hash_token("expired_token_value_1234567890"),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.session.add(expired_sess)
        db.session.commit()

        # Set expired cookie on client
        client.set_cookie("bq_learner", "expired_token_value_1234567890")

        # GET /ward: should treat as anonymous (no active learner)
        res = client.get("/ward")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        # Should not show active session badge
        assert "Session Active" not in html


def test_client_isolation(app):
    """Two independent clients have separate sessions and do not share state."""
    with app.app_context():
        client1 = app.test_client()
        client2 = app.test_client()

        res1 = client1.post("/session/start")
        res2 = client2.post("/session/start")

        cookie1 = client1.get_cookie("bq_learner").value
        cookie2 = client2.get_cookie("bq_learner").value

        assert cookie1 != cookie2

        sessions = db.session.execute(select(StudentSession)).scalars().all()
        assert len(sessions) == 2
        hashes = {s.token_hash for s in sessions}
        assert len(hashes) == 2
