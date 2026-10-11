"""Tests for database migration upgrade and idempotency."""

from __future__ import annotations

from flask_migrate import upgrade
from sqlalchemy import inspect, select
from app import create_app
from app.extensions import db
from app.models.mission import Mission


def test_migration_upgrade_on_empty_database_and_repeated_upgrade(tmp_path):
    """Verify empty database upgrades successfully via Alembic, and a second upgrade preserves data."""
    db_file = tmp_path / "migration_test.db"
    app = create_app({
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
    })

    with app.app_context():
        # 1. Upgrade empty database to head
        upgrade()

        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        expected_tables = {"missions", "student_sessions", "mission_prerequisites", "mission_progress", "alembic_version"}
        assert expected_tables.issubset(tables)

        # 2. Insert a sentinel record
        sentinel = Mission(
            slug="sentinel-room",
            room_number="999",
            title="Sentinel Room",
            availability="coming_soon",
            display_order=99,
        )
        db.session.add(sentinel)
        db.session.commit()

        # 3. Repeated upgrade should succeed cleanly without losing the sentinel record
        upgrade()

        retrieved = db.session.execute(
            select(Mission).where(Mission.room_number == "999")
        ).scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.slug == "sentinel-room"
