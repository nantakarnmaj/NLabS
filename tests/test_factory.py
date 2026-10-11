"""Tests for application factory and startup isolation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from sqlalchemy import inspect
from app import create_app
from app.extensions import db


def test_create_app_with_overrides(tmp_path):
    """Verify application factory respects configuration overrides."""
    db_file = tmp_path / "factory_test.db"
    app = create_app({
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "CUSTOM_OPTION": "enabled",
    })

    assert app.config["TESTING"] is True
    assert app.config["CUSTOM_OPTION"] == "enabled"
    assert app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{db_file}"


def test_import_and_startup_does_not_create_tables_or_seed(tmp_path):
    """Crucial requirement: creating or starting the app must NOT automatically create tables or seed data."""
    db_file = tmp_path / "unmigrated.db"
    app = create_app({
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
    })

    with app.app_context():
        # Inspect database tables without running create_all
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        # Should have 0 tables created on startup
        assert len(table_names) == 0
