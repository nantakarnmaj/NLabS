"""Test fixtures and isolation configuration for pytest.

Ensures all tests run against isolated temporary databases and never touch production or dev data.
"""

from __future__ import annotations

import re
import pytest
from flask import Flask
from flask.testing import FlaskClient
from config import TestingConfig
from app import create_app
from app.extensions import db as _db
from seed.rooms import seed_rooms


@pytest.fixture
def app(tmp_path):
    """Create and configure a clean Flask application instance for each test.

    Uses an isolated temporary SQLite database file inside tmp_path.
    """
    db_path = tmp_path / "test_breathquest.db"
    test_config = {
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret-key-for-isolated-testing-only-32char",
        "WTF_CSRF_ENABLED": False,  # disabled by default for unit tests unless explicitly enabled
        "SESSION_COOKIE_SECURE": False,
    }

    application = create_app(test_config)

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """A test client for the application."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """A test CLI runner for the application."""
    return app.test_cli_runner()


@pytest.fixture
def seeded_app(app: Flask):
    """Application fixture with rooms and prerequisites pre-seeded."""
    with app.app_context():
        seed_rooms()
    return app


@pytest.fixture
def seeded_client(seeded_app: Flask) -> FlaskClient:
    """Client connected to a pre-seeded database."""
    return seeded_app.test_client()


def extract_csrf_token(html_text: str) -> str | None:
    """Helper to extract CSRF token from rendered HTML form or meta tag."""
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_text)
    if match:
        return match.group(1)
    match_meta = re.search(r'<meta name="csrf-token" content="([^"]+)"', html_text)
    if match_meta:
        return match_meta.group(1)
    return None
